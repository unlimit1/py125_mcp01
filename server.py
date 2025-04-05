# -*- coding: utf-8 -*-
"""
YFinance MCP 서버

MCP를 사용하여 Yahoo Finance에서 주식 가격 정보를 가져오는 도구를 제공합니다.
"""

from datetime import datetime, timedelta
import pytz
from typing import Dict, List

import yfinance as yf
from pydantic import Field

from mcp.server.fastmcp import FastMCP

# MCP 서버 생성
mcp = FastMCP(
    "YFinance MCP Server", # 서버 이름
    dependencies=["yfinance", "pytz"], # 필요한 의존성 명시
)

@mcp.tool() # 이 함수를 MCP 도구로 등록
def get_current_date(timezone: str = Field(
    default="Asia/Seoul", description="시간대 (예: Asia/Seoul, America/New_York, Europe/London)"
)) -> Dict:
    """다양한 형식으로 현재 날짜 및 시간 정보를 반환합니다."""
    try:
        # 지정된 시간대의 현재 날짜/시간 가져오기
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        # 영문 요일 이름을 한글로 매핑
        day_map_kr = {
            "Monday": "월요일", "Tuesday": "화요일", "Wednesday": "수요일",
            "Thursday": "목요일", "Friday": "금요일", "Saturday": "토요일", "Sunday": "일요일"
        }
        day_en = now.strftime("%A") # 영문 전체 요일 이름
        day_kr = day_map_kr.get(day_en, day_en) # 매핑 실패 시 영문 이름 사용

        # 다양한 형식의 날짜/시간 정보 반환
        return {
            "full_datetime": now.strftime("%Y-%m-%d %H:%M:%S %Z"), # 전체 날짜/시간 (시간대 포함)
            "date_iso": now.strftime("%Y-%m-%d"), # ISO 형식 날짜
            "time_iso": now.strftime("%H:%M:%S"), # ISO 형식 시간
            "date_ymd": now.strftime("%Y-%m-%d"), # 년-월-일
            "day_of_week": day_en, # 요일 (영문)
            "day_of_week_kr": day_kr, # 요일 (한글)
            "timezone": timezone, # 사용된 시간대
            "unix_timestamp": int(now.timestamp()), # 유닉스 타임스탬프
            "year": now.year, # 년
            "month": now.month, # 월
            "day": now.day, # 일
            "hour": now.hour, # 시
            "minute": now.minute, # 분
            "second": now.second # 초
        }
    except Exception as e:
        # 날짜 정보 가져오기 중 오류 발생 시 ValueError 발생
        # 오류 처리 방식 통일 필요 (다른 함수들은 dict 반환)
        raise ValueError(f"날짜 정보를 가져오는 중 오류가 발생했습니다: {str(e)}")

@mcp.tool()
def get_stock_price(
    symbol: str = Field(description="주식 심볼 (예: AAPL, MSFT)"),
) -> Dict:
    """현재 주식 가격 정보를 가져옵니다."""
    try:
        # yfinance Ticker 객체 생성
        stock = yf.Ticker(symbol)
        # 최근 1일 데이터 가져오기
        data = stock.history(period="1d")

        # 데이터가 비어있는 경우 오류 반환
        if data.empty:
            return {"error": f"심볼 '{symbol}'에 대한 주식 데이터가 없습니다."}

        # 가장 최근 데이터 가져오기 (DataFrame의 마지막 행)
        latest = data.iloc[-1]

        # 필요한 주가 정보 반환
        return {
            "symbol": symbol, # 주식 심볼
            "date": data.index[-1].strftime("%Y-%m-%d"), # 날짜 (가장 최근 거래일)
            "open": round(latest["Open"], 2), # 시가 (소수점 2자리)
            "high": round(latest["High"], 2), # 고가 (소수점 2자리)
            "low": round(latest["Low"], 2), # 저가 (소수점 2자리)
            "close": round(latest["Close"], 2), # 종가 (소수점 2자리)
            "volume": int(latest["Volume"]) # 거래량 (정수)
        }
    except Exception as e:
        # 주가 정보 가져오기 중 오류 발생 시 오류 메시지 반환
        return {"error": f"주식 데이터를 가져오는 중 오류가 발생했습니다: {str(e)}"}

@mcp.tool()
def get_stock_price_history(
    symbol: str = Field(description="주식 심볼 (예: AAPL, MSFT)"),
    period: str = Field(
        default="1mo", # 기본 기간: 1개월
        description="기간 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)"
    ),
) -> List[Dict]:
    """지정된 기간 동안의 주식 가격 정보를 가져옵니다."""
    try:
        # yfinance Ticker 객체 생성
        stock = yf.Ticker(symbol)
        # 지정된 기간의 과거 데이터 가져오기
        data = stock.history(period=period)

        # 데이터가 비어있는 경우 오류 반환
        if data.empty:
            return [{"error": f"심볼 '{symbol}'에 대한 주식 데이터가 없습니다."}]

        # 데이터프레임을 딕셔너리 리스트로 변환
        result = []
        # 데이터프레임의 각 행(날짜별 데이터)을 순회
        for date, row in data.iterrows():
            result.append({
                "date": date.strftime("%Y-%m-%d"), # 날짜
                "open": round(row["Open"], 2), # 시가
                "high": round(row["High"], 2), # 고가
                "low": round(row["Low"], 2), # 저가
                "close": round(row["Close"], 2), # 종가
                "volume": int(row["Volume"]) # 거래량
            })
        # 결과 리스트 반환
        return result
    except Exception as e:
        # 과거 주가 정보 가져오기 중 오류 발생 시 오류 메시지 반환
        return [{"error": f"주식 데이터를 가져오는 중 오류가 발생했습니다: {str(e)}"}]

@mcp.tool()
def get_stock_info(
    symbol: str = Field(description="주식 심볼 (예: AAPL, MSFT)"),
) -> Dict:
    """주식에 대한 기본 정보를 가져옵니다."""
    try:
        # yfinance Ticker 객체 생성
        stock = yf.Ticker(symbol)
        # 주식 기본 정보 가져오기 (.info 속성)
        info = stock.info

        # 정보가 없는 경우 처리
        if not info:
            return {"error": f"심볼 '{symbol}'에 대한 정보를 찾을 수 없습니다."}

        # 필요한 정보 추출 (값이 없으면 "N/A" 반환)
        result = {
            "symbol": symbol, # 심볼
            "name": info.get("longName", "N/A"), # 전체 이름
            "sector": info.get("sector", "N/A"), # 섹터
            "industry": info.get("industry", "N/A"), # 산업
            "marketCap": info.get("marketCap", "N/A"), # 시가총액
            "previousClose": info.get("previousClose", "N/A"), # 전일 종가
            "open": info.get("open", "N/A"), # 시가
            "dayLow": info.get("dayLow", "N/A"), # 당일 저가
            "dayHigh": info.get("dayHigh", "N/A"), # 당일 고가
            "trailingPE": info.get("trailingPE", "N/A"), # 후행 PER
            "forwardPE": info.get("forwardPE", "N/A"), # 선행 PER
            # 배당 수익률 (값이 None이거나 없는 경우 "N/A" 반환)
            "dividendYield": info.get("dividendYield", "N/A") if info.get("dividendYield") is not None else "N/A",
            # 기업 개요 (최대 500자 + "...")
            "description": info.get("longBusinessSummary", "N/A")[:500] + "..." if info.get("longBusinessSummary") else "N/A",
        }
        # 결과 딕셔너리 반환
        return result
    except Exception as e:
        # 기본 정보 가져오기 중 오류 발생 시 오류 메시지 반환
        return {"error": f"주식 정보를 가져오는 중 오류가 발생했습니다: {str(e)}"}

@mcp.tool()
def search_stocks(
    query: str = Field(description="검색 키워드 (회사 이름 또는 심볼)"),
) -> List[Dict]:
    """키워드를 기반으로 주식 심볼을 검색합니다."""
    try:
        # 참고: yf.Tickers는 여러 심볼을 한 번에 처리하기 위한 것일 수 있으나,
        # 현재 로직은 쿼리를 분할하여 개별적으로 처리합니다.
        # 많은 심볼 검색 시 효율성 고려 필요.
        # tickers = yf.Tickers(query) # 이 라인은 현재 로직에서 사용되지 않음

        result = [] # 검색 결과를 저장할 리스트

        # 입력된 쿼리를 공백 기준으로 분할하여 각 심볼 처리
        for symbol_raw in query.split():
            symbol = symbol_raw.strip() # 앞뒤 공백 제거
            if not symbol: continue # 빈 문자열은 건너뛰기

            try:
                # 개별 심볼에 대한 Ticker 객체 생성
                ticker = yf.Ticker(symbol)
                info = ticker.info
                # 정보가 유효하고 주식 이름이 있는지 확인
                if info and info.get("longName"):
                    result.append({
                        "symbol": symbol, # 심볼
                        "name": info.get("longName", ""), # 이름 (기본값 빈 문자열)
                        "exchange": info.get("exchange", ""), # 거래소
                        "currency": info.get("currency", "") # 통화
                    })
            except Exception: # 개별 심볼 조회 중 발생하는 예외 처리 (보다 구체적인 예외 처리 권장)
                # 필요시 여기에 오류 로깅 추가 가능
                continue # 오류 발생 시 다음 심볼로 이동

        # 검색 결과가 있으면 결과 리스트 반환, 없으면 메시지 반환
        return result if result else [{"message": f"'{query}'에 대한 검색 결과가 없습니다."}]
    except Exception as e:
        # 전체 검색 프로세스 중 오류 발생 시 오류 메시지 반환
        return [{"error": f"주식 검색 중 오류가 발생했습니다: {str(e)}"}]

# 스크립트가 직접 실행될 때 MCP 서버 실행
if __name__ == "__main__":
    mcp.run()
