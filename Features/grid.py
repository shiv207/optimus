import streamlit as st

def add_fixed_grid():
    # Check if the sidebar is open
    sidebar_open = st.session_state.get('sidebar_open', False)

    # Adjust grid CSS based on sidebar state
    grid_css = """
    <style>
    .fixed-grid {
        position: fixed;
        bottom: 0;
        left: 0%;
        width: 0%
        height: 5vh;
        overflow: hidden;
    }
    .fixed-grid svg {
        width: 100%;
        height: 90%;
        opacity: 1; /* Adjusted base opacity */
    }
    /* iOS specific styles */
    @supports (-webkit-touch-callout: none) {
        .fixed-grid svg {
            opacity: 0.1; /* Increased opacity for iOS devices */
        }}
    /* Ensure the chat container has a higher z-index */
    .stChatFloatingInputContainer {
        z-index: 1;
        position: relative;
        background-color: transparent !important;
    }
    </style>
    """
    
    grid_svg = f"""
    <div class="fixed-grid">
        <svg width="3476" height="548" viewBox="0 0 3476 548" fill="none" xmlns="http://www.w3.org/2000/svg">
        <g clip-path="url(#clip0_92_2)">
        <path d="M1319.89 1.44769L2155.22 1.44769L3967 550.172L-490 550.172L1319.89 1.44769Z" stroke="url(#paint0_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M100.97 370.701L3374.14 370.701" stroke="url(#paint1_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M444.12 266.751L3030.98 266.751" stroke="url(#paint2_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M668.33 198.821L2806.78 198.821" stroke="url(#paint3_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M826.26 150.987L2648.85 150.987" stroke="url(#paint4_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M943.59 115.458L2531.51 115.458" stroke="url(#paint5_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M1034.09 88.0188L2441.01 88.0188" stroke="url(#paint6_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M1106.09 66.198L2369.01 66.198" stroke="url(#paint7_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M1164.74 48.436L2310.37 48.436" stroke="url(#paint8_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M1213.41 33.7124L2261.7 33.7124" stroke="url(#paint9_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M1254.45 21.2686L2220.65 21.2686" stroke="url(#paint10_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M1289.54 10.6299L2185.57 10.6299" stroke="url(#paint11_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M2085.61 1.44788L3593.83 549.707" stroke="url(#paint12_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M2016 1.44788L3222.61 549.707" stroke="url(#paint13_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M1946.39 1.44788L2851.33 549.707" stroke="url(#paint14_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M1876.78 1.44788L2480.05 549.707" stroke="url(#paint15_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M1807.17 1.44788L2108.83 549.707" stroke="url(#paint16_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M1737.55 1.44788V549.707" stroke="url(#paint17_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M1667.95 1.44788L1366.28 549.707" stroke="url(#paint18_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M1598.33 1.44788L995.05 549.707" stroke="url(#paint19_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M1528.72 1.44788L623.78 549.707" stroke="url(#paint20_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M1459.11 1.44788L252.5 549.707" stroke="url(#paint21_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        <path d="M1389.5 1.44788L-118.73 549.707" stroke="url(#paint22_linear_92_2)" stroke-width="3" stroke-linejoin="round"/>
        </g>
        <defs>
        <linearGradient id="paint0_linear_92_2" x1="-490" y1="0" x2="-490" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint1_linear_92_2" x1="100.97" y1="0" x2="100.97" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint2_linear_92_2" x1="444.12" y1="0" x2="444.12" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint3_linear_92_2" x1="668.33" y1="0" x2="668.33" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint4_linear_92_2" x1="826.26" y1="0" x2="826.26" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint5_linear_92_2" x1="943.59" y1="0" x2="943.59" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint6_linear_92_2" x1="1034.09" y1="0" x2="1034.09" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint7_linear_92_2" x1="1106.09" y1="0" x2="1106.09" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint8_linear_92_2" x1="1164.74" y1="0" x2="1164.74" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint9_linear_92_2" x1="1213.41" y1="0" x2="1213.41" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint10_linear_92_2" x1="1254.45" y1="0" x2="1254.45" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint11_linear_92_2" x1="1289.54" y1="0" x2="1289.54" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint12_linear_92_2" x1="2085.61" y1="0" x2="2085.61" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint13_linear_92_2" x1="2016" y1="0" x2="2016" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint14_linear_92_2" x1="1946.39" y1="0" x2="1946.39" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint15_linear_92_2" x1="1876.78" y1="0" x2="1876.78" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint16_linear_92_2" x1="1807.17" y1="0" x2="1807.17" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint17_linear_92_2" x1="1737.55" y1="0" x2="1737.55" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint18_linear_92_2" x1="1667.95" y1="0" x2="1667.95" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint19_linear_92_2" x1="1598.33" y1="0" x2="1598.33" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint20_linear_92_2" x1="1528.72" y1="0" x2="1528.72" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint21_linear_92_2" x1="1459.11" y1="0" x2="1459.11" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <linearGradient id="paint22_linear_92_2" x1="1389.5" y1="0" x2="1389.5" y2="548" gradientUnits="userSpaceOnUse">
            <stop offset="0" stop-color="#999999" stop-opacity="0.01"/>
            <stop offset="1" stop-color="#ffffff" stop-opacity="0.27"/>
        </linearGradient>
        <clipPath id="clip0_92_2">
        <rect width="3476" height="548" fill="white" transform="matrix(-1 0 0 -1 3476 548)"/>
        </clipPath>
        </defs>
        </svg>
    </div>
    {grid_css}
    """
    
    st.markdown(grid_svg, unsafe_allow_html=True)