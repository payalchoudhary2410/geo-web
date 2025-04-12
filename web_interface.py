import streamlit as st
import json
import pandas as pd
import time
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_crawler_v2 import WebsiteCrawler
from serach_readiness_analyser import AIReadinessAnalyzer

st.set_page_config(
    page_title="AI Search Readiness Analyzer", 
    page_icon="🔍", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("AI Search Readiness Analyzer")
    st.subheader("Optimize your website for AI assistants like Claude, ChatGPT, and Perplexity")
    
    with st.sidebar:
        st.header("Settings")
        url = st.text_input("Website URL", placeholder="https://example.com")
        max_pages = st.slider("Maximum pages to crawl", min_value=1, max_value=20, value=5)
        
        with st.expander("Advanced Options"):
            use_js = st.checkbox("Enable JavaScript rendering", value=True, 
                                help="Captures dynamically loaded content but slower")
            wait_time = st.slider("JavaScript wait time (seconds)", 
                                min_value=2, max_value=10, value=5,
                                help="Time to wait for JavaScript content to load")
        
        analyze_button = st.button("Analyze Website", type="primary", disabled=not url)
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This tool analyzes websites for AI search readiness, evaluating how well they're optimized for AI assistants like Claude, ChatGPT, and Perplexity.
        
        **Note**: This is a proof of concept demo with limited functionality.
        """)
    
    if not url:
        st.info("Enter a website URL in the sidebar to get started")
        
        # Show sample report on the main page
        st.markdown("## Sample Report Preview")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Overall Score", "68", delta=None)
        with col2:
            st.metric("Content Quality", "72", delta=None)
        with col3:
            st.metric("Technical Optimization", "65", delta=None)
        with col4:
            st.metric("AI Visibility", "59", delta=None)
            
        st.markdown("---")
        st.markdown("### How This Works")
        st.markdown("""
        1. **Crawling**: We scan your website to analyze its content and structure
        2. **Analysis**: Our algorithm evaluates multiple factors that affect AI search visibility
        3. **Recommendations**: We provide actionable suggestions to improve your website
        """)
        
        return
    
    if analyze_button:
        run_analysis(url, max_pages, use_js, wait_time)
        
def run_analysis(url, max_pages, use_js=True, wait_time=5):
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Step 1: Crawl the website
    status_text.text("Step 1/3: Crawling website...")
    
    try:
        crawler = WebsiteCrawler(url, max_pages=max_pages, 
                               use_selenium=use_js, 
                               wait_time=wait_time)
        
        # Simulate progress updates during crawling
        for i in range(1, max_pages + 1):
            # Update every second to simulate crawling progress
            time.sleep(0.5)
            progress_value = 0.3 * (i / max_pages)
            progress_bar.progress(progress_value)
            status_text.text(f"Step 1/3: Crawling page {i}/{max_pages}...")
            
        crawler_results = crawler.crawl()
        
        # Step 2: Analyze for AI readiness
        status_text.text("Step 2/3: Analyzing AI search readiness...")
        progress_bar.progress(0.4)
        
        analyzer = AIReadinessAnalyzer(crawler_results)
        
        # Simulate progress for analysis phases
        status_text.text("Step 2/3: Analyzing content quality...")
        progress_bar.progress(0.5)
        analyzer.analyze_content_quality()
        
        status_text.text("Step 2/3: Analyzing technical optimization...")
        progress_bar.progress(0.6)
        analyzer.analyze_technical_optimization()
        
        status_text.text("Step 2/3: Analyzing authority signals...")
        progress_bar.progress(0.7)
        analyzer.analyze_authority_signals()
        
        status_text.text("Step 2/3: Analyzing question answering capabilities...")
        progress_bar.progress(0.8)
        analyzer.analyze_question_answering()
        
        # Step 3: Generate report
        status_text.text("Step 3/3: Generating report...")
        progress_bar.progress(0.9)
        report_data = analyzer.generate_report()
        
        # Complete
        progress_bar.progress(1.0)
        status_text.text("Analysis complete!")
        time.sleep(1)
        
        # Clear progress indicators
        status_text.empty()
        progress_bar.empty()
        
        # Display the report
        display_report(report_data)
        
    except Exception as e:
        st.error(f"Error analyzing website: {str(e)}")
        
def display_report(report_data):
    scores = report_data["ai_readiness_scores"]
    site_info = report_data["site_info"]
    content_stats = report_data["content_stats"]
    recommendations = report_data["top_recommendations"]
    
    st.header(f"AI Search Readiness Report: {site_info['domain']}")
    
    # Overall score and component scores
    st.subheader("Readiness Scores")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Overall Score", f"{scores['overall']:.1f}", delta=None)
    with col2:
        st.metric("Content Quality", f"{scores['components']['content_quality']:.1f}", delta=None)
    with col3:
        st.metric("Technical", f"{scores['components']['technical_optimization']:.1f}", delta=None)
    with col4:
        st.metric("Authority", f"{scores['components']['authority_signals']:.1f}", delta=None)
    with col5:
        st.metric("Q&A Capability", f"{scores['components']['question_answering']:.1f}", delta=None)
    
    # Site information
    st.subheader("Website Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Content Statistics")
        stats_df = pd.DataFrame({
            "Metric": [
                "Pages Analyzed", 
                "Average Word Count", 
                "Pages with Thin Content",
                "Q&A Pairs Found",
                "Has Structured Data",
                "Pages with JS Content"
            ],
            "Value": [
                content_stats["total_pages"],
                f"{content_stats['avg_word_count']:.1f}",
                content_stats["pages_with_thin_content"],
                content_stats["total_qa_pairs"],
                "Yes" if content_stats["has_structured_data"] else "No",
                content_stats.get("js_rendered_pages", 0)
            ]
        })
        st.table(stats_df)
        
    with col2:
        st.markdown("#### Site Details")
        site_df = pd.DataFrame({
            "Property": ["Site Title", "Site Description"],
            "Value": [
                site_info.get("title", "Not found"),
                site_info.get("description", "Not found")
            ]
        })
        st.table(site_df)
    
    # Recommendations
    st.subheader("Top Recommendations")
    
    for i, rec in enumerate(recommendations, 1):
        importance_color = {
            "Critical": "red",
            "High": "orange",
            "Medium": "blue"
        }.get(rec["importance"], "gray")
        
        with st.expander(f"{i}. {rec['issue']} ({rec['category']})"):
            st.markdown(f"**Importance:** :{importance_color}[{rec['importance']}]")
            st.markdown(f"**Recommendation:** {rec['recommendation']}")
    
    # Raw data
    with st.expander("View Raw JSON Data"):
        st.json(report_data)

if __name__ == "__main__":
    main()