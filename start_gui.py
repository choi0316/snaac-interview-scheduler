#!/usr/bin/env python3
"""
면접 스케줄링 시스템 GUI 런처
"""
import os
import sys
import subprocess

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    """GUI 시작"""
    print("🚀 면접 스케줄링 시스템 GUI 시작")
    print("=" * 60)
    print()
    
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "simple_gui.py",
        "--server.port=8501",
        "--server.headless=false",
        "--browser.gatherUsageStats=false"
    ]
    
    print("🌐 웹 브라우저에서 다음 주소로 접속하세요:")
    print("   http://localhost:8501")
    print()
    print("종료하려면 Ctrl+C를 누르세요.")
    print("=" * 60)
    
    try:
        subprocess.run(cmd, cwd=project_root)
    except KeyboardInterrupt:
        print("\n\n✅ GUI 종료됨")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
