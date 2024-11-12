import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import re

def parse_log_line(line):
    try:
        # Extract timestamp and message
        timestamp_str = line.split(": ")[0]
        message = ": ".join(line.split(": ")[1:])
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
        return timestamp, message
    except:
        return None, None

def extract_oi_data(message):
    if "ATM CE OI:" in message:
        values = re.findall(r"OI:(\d+)", message)
        if len(values) >= 2:
            return int(values[0]), int(values[1])
    return None, None

def extract_strike_data(message):
    if "ATM strikes:" in message:
        strikes = re.findall(r"BANKNIFTY\d+[NF]\d+(\d+)(CE|PE)", message)
        if strikes:
            return strikes[0][0]
    return None

def process_log_data(log_text):
    lines = log_text.split('\n')
    data = []
    
    for line in lines:
        timestamp, message = parse_log_line(line)
        if timestamp:
            ce_oi, pe_oi = extract_oi_data(message)
            strike = extract_strike_data(message)
            
            if ce_oi is not None and pe_oi is not None:
                data.append({
                    'timestamp': timestamp,
                    'ce_oi': ce_oi,
                    'pe_oi': pe_oi,
                    'oi_difference': ce_oi - pe_oi
                })
            
            if strike:
                data.append({
                    'timestamp': timestamp,
                    'strike': strike
                })
    
    return pd.DataFrame(data)

def main():
    st.title("Trading Analysis Dashboard")
    
    # File upload
    uploaded_file = st.file_uploader("Upload trading log file", type=['txt', 'log'])
    
    if uploaded_file:
        log_text = uploaded_file.getvalue().decode()
        df = process_log_data(log_text)
        
        if not df.empty:
            # OI Analysis Section
            st.header("Open Interest Analysis")
            
            # OI Time Series Plot
            fig = go.Figure()
            
            if 'ce_oi' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['ce_oi'],
                    name='CE OI',
                    line=dict(color='green')
                ))
                
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['pe_oi'],
                    name='PE OI',
                    line=dict(color='red')
                ))
                
                fig.update_layout(
                    title='CE vs PE Open Interest Over Time',
                    xaxis_title='Time',
                    yaxis_title='Open Interest',
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig)
                
                # OI Difference Plot
                fig_diff = go.Figure()
                fig_diff.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['oi_difference'],
                    name='OI Difference',
                    line=dict(color='blue')
                ))
                
                fig_diff.update_layout(
                    title='CE-PE Open Interest Difference Over Time',
                    xaxis_title='Time',
                    yaxis_title='OI Difference',
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_diff)
            
            # Strike Price Analysis
            if 'strike' in df.columns:
                st.header("Strike Price Analysis")
                strike_df = df[df['strike'].notna()]
                
                if not strike_df.empty:
                    fig_strike = go.Figure()
                    fig_strike.add_trace(go.Scatter(
                        x=strike_df['timestamp'],
                        y=strike_df['strike'],
                        name='ATM Strike',
                        mode='lines+markers'
                    ))
                    
                    fig_strike.update_layout(
                        title='ATM Strike Price Changes Over Time',
                        xaxis_title='Time',
                        yaxis_title='Strike Price',
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_strike)
            
            # Summary Statistics
            st.header("Summary Statistics")
            if 'ce_oi' in df.columns:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Avg CE OI", f"{df['ce_oi'].mean():,.0f}")
                
                with col2:
                    st.metric("Avg PE OI", f"{df['pe_oi'].mean():,.0f}")
                
                with col3:
                    st.metric("Avg OI Diff", f"{df['oi_difference'].mean():,.0f}")
        else:
            st.warning("No valid data found in the log file.")

if __name__ == "__main__":
    main()
