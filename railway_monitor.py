#!/usr/bin/env python3
"""
Railway Usage Monitor
Tracks system usage and provides recommendations for staying within free tier
"""

import datetime
import json
import os

class RailwayMonitor:
    def __init__(self):
        self.usage_file = "railway_usage.json"
        self.load_usage_data()
    
    def load_usage_data(self):
        """Load existing usage data"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    self.usage_data = json.load(f)
            else:
                self.usage_data = {
                    "month_start": datetime.datetime.now().strftime("%Y-%m-01"),
                    "total_hours": 0,
                    "daily_usage": {},
                    "recommendations": []
                }
        except Exception:
            self.usage_data = {
                "month_start": datetime.datetime.now().strftime("%Y-%m-01"),
                "total_hours": 0,
                "daily_usage": {},
                "recommendations": []
            }
    
    def save_usage_data(self):
        """Save usage data to file"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            print(f"Error saving usage data: {e}")
    
    def record_session(self, hours=1):
        """Record a usage session"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.usage_data["daily_usage"]:
            self.usage_data["daily_usage"][today] = 0
        
        self.usage_data["daily_usage"][today] += hours
        self.usage_data["total_hours"] += hours
        self.save_usage_data()
    
    def get_monthly_projection(self):
        """Project monthly usage based on current pattern"""
        now = datetime.datetime.now()
        days_in_month = (datetime.datetime(now.year, now.month + 1, 1) - 
                        datetime.datetime(now.year, now.month, 1)).days
        current_day = now.day
        
        if current_day > 0:
            daily_avg = self.usage_data["total_hours"] / current_day
            projected_monthly = daily_avg * days_in_month
        else:
            projected_monthly = 0
        
        return projected_monthly
    
    def get_recommendations(self):
        """Get usage recommendations"""
        projected = self.get_monthly_projection()
        recommendations = []
        
        if projected > 500:
            recommendations.extend([
                "⚠️  PROJECTED USAGE EXCEEDS 500h FREE LIMIT",
                "🔧 Enable aggressive auto-sleep",
                "⏰ Limit usage to business hours only",
                "💾 Ensure daily backups to Google Drive",
                "🔄 Consider Railway Pro ($5/month) if needed"
            ])
        elif projected > 400:
            recommendations.extend([
                "⚠️  Usage approaching limit (400h+)",
                "🔧 Monitor usage more closely", 
                "⏰ Optimize for business hours",
                "💾 Daily backups recommended"
            ])
        else:
            recommendations.extend([
                "✅ Usage within safe limits",
                "🔧 Current optimization working",
                "💾 Continue regular backups"
            ])
        
        return recommendations
    
    def display_status(self):
        """Display current usage status"""
        projected = self.get_monthly_projection()
        recommendations = self.get_recommendations()
        
        print("\n📊 RAILWAY USAGE MONITOR")
        print("=" * 40)
        print(f"Month: {datetime.datetime.now().strftime('%B %Y')}")
        print(f"Current Usage: {self.usage_data['total_hours']:.1f} hours")
        print(f"Projected Monthly: {projected:.1f} hours")
        print(f"Free Tier Limit: 500 hours")
        print(f"Remaining Budget: {500 - projected:.1f} hours")
        
        if projected <= 500:
            print("🟢 Status: WITHIN FREE TIER LIMIT")
        else:
            print("🔴 Status: EXCEEDING FREE TIER LIMIT")
        
        print("\n💡 RECOMMENDATIONS:")
        for rec in recommendations:
            print(f"  {rec}")
        
        print("\n📈 DAILY USAGE (Last 7 days):")
        recent_days = sorted(self.usage_data["daily_usage"].items())[-7:]
        for date, hours in recent_days:
            print(f"  {date}: {hours:.1f}h")

def main():
    monitor = RailwayMonitor()
    
    # Record current session (estimate 1 hour)
    monitor.record_session(1.0)
    
    # Display status
    monitor.display_status()
    
    print(f"\n📝 Usage data saved to: {monitor.usage_file}")
    print("💡 Run this script daily to track usage")

if __name__ == "__main__":
    main()