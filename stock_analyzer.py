"""
Stock Analyzer - ML Price Prediction and AI Market Analysis

Provides machine learning price predictions and natural language market insights
for the Single Ticker Audit view.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')


class StockAnalyzer:
    """ML-powered stock analysis with price prediction and market insights."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators using pure pandas/numpy."""
        df = data.copy()
        
        # Simple Moving Averages
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # Exponential Moving Averages
        df['EMA_12'] = df['Close'].ewm(span=12).mean()
        df['EMA_26'] = df['Close'].ewm(span=26).mean()
        
        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        
        # Volume indicators
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_ratio'] = df['Volume'] / df['Volume_SMA']
        
        # Price-based indicators
        df['High_Low_Pct'] = (df['High'] - df['Low']) / df['Close'] * 100
        df['Price_Change'] = df['Close'] - df['Open']
        df['Price_Change_Pct'] = (df['Close'] - df['Open']) / df['Open'] * 100
        
        # ATR (Average True Range)
        df['High_Low'] = df['High'] - df['Low']
        df['High_Close'] = np.abs(df['High'] - df['Close'].shift())
        df['Low_Close'] = np.abs(df['Low'] - df['Close'].shift())
        df['True_Range'] = df[['High_Low', 'High_Close', 'Low_Close']].max(axis=1)
        df['ATR_calc'] = df['True_Range'].rolling(window=14).mean()
        
        # Stochastic Oscillator
        low_14 = df['Low'].rolling(window=14).min()
        high_14 = df['High'].rolling(window=14).max()
        df['Stoch_K'] = 100 * ((df['Close'] - low_14) / (high_14 - low_14))
        df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
        
        return df
    
    def prepare_ml_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for machine learning with reduced data requirements."""
        df = data.copy()
        
        # Returns and momentum
        df['Returns'] = df['Close'].pct_change()
        df['Returns_5d'] = df['Close'].pct_change(5)
        df['Returns_10d'] = df['Close'].pct_change(10)
        
        # Lag features (reduced lag periods for smaller datasets)
        for lag in [1, 2, 3, 5]:
            df[f'Close_lag_{lag}'] = df['Close'].shift(lag)
            df[f'Volume_lag_{lag}'] = df['Volume'].shift(lag)
            df[f'Returns_lag_{lag}'] = df['Returns'].shift(lag)
        
        # Rolling statistics (reduced windows)
        for window in [5, 10, 20]:
            df[f'Close_mean_{window}'] = df['Close'].rolling(window).mean()
            df[f'Close_std_{window}'] = df['Close'].rolling(window).std()
            df[f'Volume_mean_{window}'] = df['Volume'].rolling(window).mean()
        
        # Price position relative to moving averages
        if 'SMA_20' in df.columns:
            df['Price_vs_SMA20'] = (df['Close'] - df['SMA_20']) / df['SMA_20'] * 100
        if 'SMA_50' in df.columns:
            df['Price_vs_SMA50'] = (df['Close'] - df['SMA_50']) / df['SMA_50'] * 100
        
        # Volatility features
        df['Price_volatility_10d'] = df['Returns'].rolling(10).std()
        df['Price_volatility_20d'] = df['Returns'].rolling(20).std()
        
        return df
    
    def train_prediction_model(self, data: pd.DataFrame, horizon: int = 5) -> Optional[Dict[str, Any]]:
        """Train ML model for price prediction with configurable horizon.
        
        Args:
            data: DataFrame with OHLCV and technical indicators
            horizon: Prediction horizon in days (default 5 for week-ahead)
        """
        df = self.prepare_ml_features(data)
        df = df.dropna()
        
        # Reduced minimum data requirement (50 instead of 100)
        if len(df) < 50:
            return None
        
        # Features for prediction
        exclude_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits', 
                       'Returns', 'Returns_5d', 'Returns_10d', 'High_Low', 'High_Close', 
                       'Low_Close', 'True_Range', 'Price_Change', 'EMA_12', 'EMA_26']
        
        feature_cols = [col for col in df.columns if not any(exc in col for exc in exclude_cols)]
        feature_cols = [col for col in feature_cols if 
                       'lag' in col or 'mean' in col or 'std' in col or 
                       col in ['RSI', 'MACD', 'Price_vs_SMA20', 'Price_vs_SMA50', 
                              'Price_volatility_10d', 'Price_volatility_20d', 'ATR_calc',
                              'Stoch_K', 'Volume_ratio', 'MACD_histogram']]
        
        if len(feature_cols) < 5:
            return None
        
        X = df[feature_cols].ffill().bfill()
        # Use 5-day forward close for more stable prediction
        y = df['Close'].shift(-horizon)
        
        # Remove rows without target and any remaining NaN
        X = X[:-horizon]
        y = y[:-horizon]
        
        # Remove any remaining NaN values
        mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[mask]
        y = y[mask]
        
        if len(X) < 30:
            return None
        
        # Split and train
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.model.fit(X_train_scaled, y_train)
        
        # Calculate accuracy
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        # Get top feature importances
        importance = dict(zip(feature_cols, self.model.feature_importances_))
        top_features = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5])
        
        # Store last features for prediction (use the most recent complete row)
        last_features = df[feature_cols].iloc[-1:].ffill().bfill()
        
        return {
            'train_score': train_score,
            'test_score': test_score,
            'feature_importance': top_features,
            'last_features': last_features,
            'feature_cols': feature_cols,
            'horizon': horizon
        }
    
    def predict_price_range(self, model_info: Optional[Dict], current_price: float) -> Optional[Dict[str, float]]:
        """Predict price range using Random Forest tree variance.
        
        Returns a dict with:
            - expected: Mean prediction from all trees
            - low: Lower bound (1 std dev below mean)
            - high: Upper bound (1 std dev above mean)
            - confidence: Inverse of relative std dev
        """
        if model_info is None:
            return None
        
        try:
            last_features_scaled = self.scaler.transform(model_info['last_features'])
            
            # Get predictions from all individual trees for uncertainty estimation
            tree_predictions = np.array([tree.predict(last_features_scaled)[0] 
                                         for tree in self.model.estimators_])
            
            # Calculate statistics
            expected = np.mean(tree_predictions)
            std_dev = np.std(tree_predictions)
            
            # Use 1 standard deviation for ~68% confidence interval
            low = expected - std_dev
            high = expected + std_dev
            
            # Confidence is inversely related to relative uncertainty
            # Lower relative std = higher confidence
            relative_std = std_dev / expected if expected > 0 else 0
            confidence = max(0, min(1, 1 - (relative_std * 10)))  # Scale to 0-1
            
            # Calculate change percentages
            expected_change_pct = ((expected - current_price) / current_price) * 100
            low_change_pct = ((low - current_price) / current_price) * 100
            high_change_pct = ((high - current_price) / current_price) * 100
            
            return {
                'expected': expected,
                'low': low,
                'high': high,
                'expected_change_pct': expected_change_pct,
                'low_change_pct': low_change_pct,
                'high_change_pct': high_change_pct,
                'confidence': confidence,
                'horizon': model_info.get('horizon', 5)
            }
        except Exception as e:
            print(f"Prediction error: {e}")
            return None


def generate_market_analysis(data: pd.DataFrame, ticker: str) -> List[str]:
    """Generate AI-powered market analysis insights."""
    if data.empty or len(data) < 20:
        return ["⚠️ Insufficient data for comprehensive analysis"]
    
    latest = data.iloc[-1]
    prev = data.iloc[-2]
    
    # Price movement
    price_change = latest['Close'] - prev['Close']
    price_change_pct = (price_change / prev['Close']) * 100
    
    # Technical values with fallbacks
    rsi = latest.get('RSI', 50)
    sma_20 = latest.get('SMA_20', latest['Close'])
    sma_50 = latest.get('SMA_50', latest['Close'])
    bb_upper = latest.get('BB_upper', latest['Close'])
    bb_lower = latest.get('BB_lower', latest['Close'])
    macd = latest.get('MACD', 0)
    macd_signal = latest.get('MACD_signal', 0)
    
    # Volume analysis
    avg_volume = data['Volume'].rolling(20).mean().iloc[-1] if len(data) >= 20 else data['Volume'].mean()
    volume_ratio = latest['Volume'] / avg_volume if avg_volume > 0 else 1
    
    # Generate analysis
    analysis = []
    
    # Price trend
    if price_change_pct > 3:
        analysis.append(f"🚀 {ticker} shows exceptional bullish momentum with a {price_change_pct:.2f}% surge")
    elif price_change_pct > 1:
        analysis.append(f"🟢 {ticker} demonstrates strong upward movement (+{price_change_pct:.2f}%)")
    elif price_change_pct > 0:
        analysis.append(f"🟡 {ticker} shows modest gains (+{price_change_pct:.2f}%)")
    elif price_change_pct > -1:
        analysis.append(f"🟡 {ticker} experiences slight decline ({price_change_pct:.2f}%)")
    elif price_change_pct > -3:
        analysis.append(f"🔴 {ticker} shows moderate bearish pressure ({price_change_pct:.2f}%)")
    else:
        analysis.append(f"🔻 {ticker} faces significant selling pressure ({price_change_pct:.2f}%)")
    
    # RSI analysis
    if pd.notna(rsi):
        if rsi > 80:
            analysis.append(f"🚨 RSI at {rsi:.1f} indicates severely overbought conditions - potential reversal ahead")
        elif rsi > 70:
            analysis.append(f"⚠️ RSI at {rsi:.1f} shows overbought territory - exercise caution")
        elif rsi < 20:
            analysis.append(f"🛒 RSI at {rsi:.1f} signals severely oversold - strong buying opportunity")
        elif rsi < 30:
            analysis.append(f"💡 RSI at {rsi:.1f} suggests oversold conditions - potential buying opportunity")
        elif 40 <= rsi <= 60:
            analysis.append(f"⚖️ RSI at {rsi:.1f} indicates balanced momentum")
        else:
            analysis.append(f"📊 RSI at {rsi:.1f} shows {'bullish' if rsi > 50 else 'bearish'} bias")
    
    # Moving average analysis
    current_price = latest['Close']
    if pd.notna(sma_20) and pd.notna(sma_50):
        if current_price > sma_20 > sma_50:
            analysis.append("📈 Strong bullish alignment - price above both 20 and 50-day MAs")
        elif current_price < sma_20 < sma_50:
            analysis.append("📉 Bearish trend confirmed - price below key moving averages")
        elif current_price > sma_20 and sma_20 < sma_50:
            analysis.append("🔄 Mixed signals - short-term bullish but longer-term bearish")
        else:
            analysis.append("➡️ Consolidation phase - awaiting directional breakout")
    
    # Bollinger Bands analysis
    if pd.notna(bb_upper) and pd.notna(bb_lower):
        if current_price > bb_upper:
            analysis.append("📊 Price trading above upper Bollinger Band - potential overbought")
        elif current_price < bb_lower:
            analysis.append("📊 Price near lower Bollinger Band - potential oversold bounce")
    
    # MACD analysis
    if pd.notna(macd) and pd.notna(macd_signal):
        if macd > macd_signal and macd > 0:
            analysis.append("⚡ MACD shows strong bullish momentum")
        elif macd < macd_signal and macd < 0:
            analysis.append("⚡ MACD indicates bearish momentum")
        elif macd > macd_signal:
            analysis.append("⚡ MACD bullish crossover - momentum improving")
        else:
            analysis.append("⚡ MACD bearish crossover - momentum weakening")
    
    # Volume analysis
    if volume_ratio > 2:
        analysis.append("🔥 Exceptional volume surge confirms strong conviction")
    elif volume_ratio > 1.5:
        analysis.append("📊 High volume validates price movement")
    elif volume_ratio < 0.5:
        analysis.append("📊 Below-average volume suggests weak conviction")
    else:
        analysis.append("📊 Normal volume levels")
    
    return analysis
