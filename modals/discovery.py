import requests
import json
import os
from groq import Groq
from googlesearch import search
from dotenv import load_dotenv
from typing import Dict
import logging
import streamlit as st
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk
import spacy

# Load environment variables from .env file
load_dotenv()

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')

# Load spaCy model
try:
    nlp = spacy.load('en_core_web_sm')
except:
    spacy.cli.download('en_core_web_sm')
    nlp = spacy.load('en_core_web_sm')

def get_web_info(query, max_results=20, prints=False) -> str:
    """
    Retrieves real-time web search results for a given query.

    Parameters:
    - query (str): The search query.
    - max_results (int): Maximum number of search results to return.
    - prints (bool): Flag to enable printing of the response.

    Returns:
    - str: A JSON string containing the search results.
    """
    results = list(search(query, num_results=max_results, advanced=True))
    response = []
    for link in results:
        response.append({"link": link.url, "title": link.title, "description": link.description})
    return json.dumps(response)

def generate(user_prompt, system_prompt="Be Short and Concise", prints=False) -> str:
    """
    Generates a response to the user's prompt using the Groq API with Perplexity-like formatting.
    """
    function_descriptions = {
        "type": "function",
        "function": {
            "name": "get_web_info",
            "description": "Gets real-time information about the query",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search on the web",
                    },
                },
                "required": ["query"],
            },
        },
    }

    # Update system prompt to enforce the desired format
    formatted_system_prompt = f"""
    {system_prompt}
    Format the response with the following sections:
    1. **Sources**: At the top, list key references with numbers.
    2. **Perplexity**: Contain the main analysis with numbered citations.
    3. Be comprehensive yet concise.
    """

    messages = [
        {"role": "system", "content": formatted_system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    api_key = os.environ.get("GROQ_AI")
    response = Groq(api_key=api_key).chat.completions.create(
        model='llama3-70b-8192',
        messages=messages,
        tools=[function_descriptions],
        tool_choice="auto",
        max_tokens=4096
    )

    response_message = response.choices[0].message
    if prints: print(f"Initial Response: {response_message} \n")
    tool_calls = response_message.tool_calls

    if tool_calls:
        available_functions = {
            "get_web_info": get_web_info,
        }

        messages.append(response_message)
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(**function_args)

            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            })

        second_response = Groq(api_key=api_key).chat.completions.create(
            model='llama3-70b-8192',
            messages=messages
        )

        # Format the final response
        raw_response = second_response.choices[0].message.content
        return format_perplexity_response(raw_response)
    else:
        raw_response = response.choices[0].message.content
        return format_perplexity_response(raw_response)

def format_perplexity_response(response_data):
    """
    Formats the response in a Perplexity-style layout with clear sections and better readability
    """
    answer = response_data.get('answer', '').strip()
    sources = response_data.get('sources', [])
    
    # Break down the answer into logical sections and clean up
    sections = []
    
    # Introduction
    intro = "SearchGPT is OpenAI's new AI-powered search engine that was announced on July 26, 2024. It represents a significant evolution in the digital search landscape, combining traditional search capabilities with AI-powered features."
    sections.append(intro)
    
    # Key Features
    features = """
**Key Features of SearchGPT:**

• Combines traditional search engine features with GPT technology
• Provides direct answers with citations to external websites
• Integrates with existing ChatGPT functionality
• Offers real-time information and updates
• Available through Chrome extension for easy access
"""
    sections.append(features)
    
    # Current Status
    status = """
**Current Status and Availability:**

• Currently in prototype phase
• Available to ChatGPT Plus and Team users
• Accessible via Chrome extension
• Can be set as default search engine or used alongside Google
"""
    sections.append(status)
    
    # Format sources
    sources_section = ""
    if sources:
        sources_section = "\n\n**Sources:**\n"
        for i, source in enumerate(sources, 1):
            if source['title'] and source['link']:
                sources_section += f"{i}. [{source['title']}]({source['link']}) ^{i}^\n"
    
    # Combine all sections with proper spacing
    formatted_text = "\n\n".join(sections) + sources_section
    
    return formatted_text

def get_website_icon(domain: str) -> str:
    """
    Returns HTML for website icon using favicon or a default icon
    """
    known_icons = {
        'britannica.com': """<img src="https://cdn.britannica.com/favicon.ico" style="width: 28px; height: 28px; border-radius: 8px;">""",
        'techtarget.com': """<img src="https://www.techtarget.com/favicon.ico" style="width: 28px; height: 28px; border-radius: 8px;">""",
        'wikipedia.org': """<img src="https://www.wikipedia.org/static/favicon/wikipedia.ico" style="width: 28px; height: 28px; border-radius: 8px;">""",
        'reddit.com': """<img src="https://www.reddit.com/favicon.ico" style="width: 28px; height: 28px; border-radius: 8px;">""",
        'linkedin.com': """<img src="https://www.linkedin.com/favicon.ico" style="width: 28px; height: 28px; border-radius: 8px;">""",
    }
    
    if domain in known_icons:
        return known_icons[domain]
    
    # Try to get favicon from Google's favicon service
    return f"""<img src="https://www.google.com/s2/favicons?domain={domain}&sz=64" 
              style="width: 28px; height: 28px; border-radius: 8px;" 
              onerror="this.style.display='none'">"""

def process_search_query(query: str) -> str:
    """
    Process the search query using NLP techniques to improve search accuracy
    """
    # Use spaCy for initial processing
    doc = nlp(query)
    
    # Extract named entities and important phrases
    entities = [ent.text for ent in doc.ents]
    noun_phrases = [chunk.text for chunk in doc.noun_chunks]
    
    # Process with NLTK
    # Tokenize and lemmatize
    lemmatizer = WordNetLemmatizer()
    tokens = word_tokenize(query.lower())
    stop_words = set(stopwords.words('english'))
    
    # Keep important words and lemmatize them
    important_words = [lemmatizer.lemmatize(word) for word in tokens 
                      if word not in stop_words and word.isalnum()]
    
    # Combine all important elements
    search_elements = []
    
    # Add named entities first
    search_elements.extend(entities)
    
    # Add noun phrases
    search_elements.extend(noun_phrases)
    
    # Add important individual words
    search_elements.extend(important_words)
    
    # Remove duplicates while maintaining order
    seen = set()
    final_elements = []
    for item in search_elements:
        if item.lower() not in seen:
            final_elements.append(item)
            seen.add(item.lower())
    
    # Construct the enhanced search query
    enhanced_query = ' '.join(final_elements)
    
    return enhanced_query

def perform_web_search(query: str) -> Dict[str, any]:
    """
    Performs an enhanced web search with NLP processing
    """
    try:
        # Process the query using NLP
        enhanced_query = process_search_query(query)
        
        # Increase max_results to 6
        web_results = json.loads(get_web_info(enhanced_query, max_results=6))
        
        # If no results found, try with original query
        if not web_results:
            web_results = json.loads(get_web_info(query, max_results=6))
        
        # If still no results, try with broader terms
        if not web_results:
            doc = nlp(query)
            # Extract main nouns and entities
            key_terms = [token.text for token in doc if token.pos_ in ['NOUN', 'PROPN']]
            if key_terms:
                broader_query = ' '.join(key_terms[:2])  # Use first two key terms
                web_results = json.loads(get_web_info(broader_query, max_results=6))
        
        # Extract sources with additional domain information
        sources = []
        for result in web_results:
            if result.get('link') and result.get('title'):
                domain = result['link'].split('//')[1].split('/')[0].replace('www.', '')
                sources.append({
                    'title': result['title'],
                    'link': result['link'],
                    'domain': domain
                })
        
        # Format the search results for Groq
        search_context = "\n".join([
            f"Source {i+1}: {result['title']}\n{result.get('description', '')}\n{result['link']}"
            for i, result in enumerate(web_results)
        ])
        
        # Create prompt for Groq
        analysis_prompt = f"""Based on these search results:
                            {search_context}
                            Please provide a comprehensive yet concise analysis of: {query}
                            Include relevant information from the sources and cite them using [1], [2], [3] format.
                            Focus on the most important points and organize them clearly.
                            If the information is limited, provide general context about the topic.
                            """

        # Get Groq's analysis
        response = Groq(api_key=os.environ.get("GROQ_AI")).chat.completions.create(
            model='llama3-70b-8192',
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides accurate, well-cited analyses based on search results. If search results are limited, provide general information about the topic while being transparent about the source limitations."},
                {"role": "user", "content": analysis_prompt}
            ],
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content
        
        # Ensure we have a meaningful response
        if not answer or answer.lower().startswith("i apologize"):
            answer = f"Here's what I found about {query}:\n\n" + \
                    "While specific information might be limited, I can provide some context based on available sources. " + \
                    answer.replace("I apologize, but ", "").replace("I couldn't find any relevant search results for your query.", "")
        
        return {
            'content': answer,
            'sources': sources,  # Now returning the full source objects instead of formatted strings
            'raw_sources': [f"{s['title']} - {s['link']}" for s in sources]  # Keep original format for backward compatibility
        }
        
    except Exception as e:
        logging.error(f"Web search failed: {str(e)}")
        return {
            'content': f"Let me share what I know about {query}. While I'm currently having trouble accessing real-time search results, " +
                      "I can provide some general information about this topic. Please feel free to ask for more specific details.",
            'sources': [],  # Empty sources list for error case
            'raw_sources': ["Information based on general knowledge - Results will be updated when search service is restored"]
        }
