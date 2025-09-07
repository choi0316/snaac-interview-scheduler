#!/usr/bin/env python3
"""
면접 스케줄링 시스템 종합 테스트 실행기

이 스크립트는 전체 시스템의 테스트를 체계적으로 실행하고
상세한 보고서를 생성합니다.

사용법:
    python run_tests.py                  # 전체 테스트 실행
    python run_tests.py --fast           # 빠른 테스트만 실행  
    python run_tests.py --integration    # 통합 테스트만 실행
    python run_tests.py --performance    # 성능 테스트만 실행
    python run_tests.py --coverage       # 코드 커버리지 포함
"""

import sys
import os
import subprocess
import time
import argparse
from pathlib import Path
import json

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestRunner:
    """테스트 실행 관리자"""
    
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.test_dir = self.project_root / "tests"
        self.results = {}
        
    def run_command(self, command, capture_output=True):
        """명령어 실행"""
        try:
            if capture_output:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    cwd=self.project_root
                )
                return result.returncode, result.stdout, result.stderr
            else:
                result = subprocess.run(command, shell=True, cwd=self.project_root)
                return result.returncode, "", ""
        except Exception as e:
            return 1, "", str(e)
    
    def check_dependencies(self):
        """의존성 확인"""
        print("🔍 의존성 확인 중...")
        
        # pytest 설치 확인
        returncode, stdout, stderr = self.run_command("python -m pytest --version")
        if returncode != 0:
            print("❌ pytest가 설치되지 않았습니다. 설치 중...")
            self.run_command("pip install pytest", capture_output=False)
        else:
            print(f"✅ pytest 설치됨: {stdout.strip()}")
        
        # 필수 패키지 확인
        required_packages = [
            "pdfplumber", "ortools", "openpyxl", "streamlit", 
            "jinja2", "pytest-cov", "pytest-html", "psutil"
        ]
        
        missing_packages = []
        for package in required_packages:
            returncode, _, _ = self.run_command(f"python -c 'import {package.replace('-', '_')}'")
            if returncode != 0:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"⚠️  누락된 패키지: {', '.join(missing_packages)}")
            print("📦 requirements.txt에서 설치 중...")
            self.run_command("pip install -r requirements.txt", capture_output=False)
        else:
            print("✅ 모든 의존성이 설치되어 있습니다.")
    
    def run_unit_tests(self):
        """단위 테스트 실행"""
        print("\n🧪 단위 테스트 실행 중...")
        
        unit_test_files = [
            "test_models.py",
            "test_pdf_extractor.py", 
            "test_scheduler_engine.py",
            "test_excel_generator.py",
            "test_email_system.py"
        ]
        
        start_time = time.time()
        total_passed = 0
        total_failed = 0
        
        for test_file in unit_test_files:
            test_path = self.test_dir / test_file
            if test_path.exists():
                print(f"  📋 {test_file} 테스트 중...")
                
                command = f"python -m pytest {test_path} -v --tb=short"
                returncode, stdout, stderr = self.run_command(command)
                
                # 결과 파싱
                if "failed" in stdout.lower():
                    failed = int(stdout.split("failed")[0].split()[-1]) if "failed" in stdout else 0
                else:
                    failed = 0
                
                if "passed" in stdout.lower():
                    passed = int(stdout.split("passed")[0].split()[-1]) if "passed" in stdout else 0
                else:
                    passed = 0
                
                total_passed += passed
                total_failed += failed
                
                if returncode == 0:
                    print(f"    ✅ {test_file}: {passed}개 통과")
                else:
                    print(f"    ❌ {test_file}: {passed}개 통과, {failed}개 실패")
        
        unit_test_time = time.time() - start_time
        
        self.results['unit_tests'] = {
            'passed': total_passed,
            'failed': total_failed,
            'time': unit_test_time
        }
        
        print(f"📊 단위 테스트 완료: {total_passed}개 통과, {total_failed}개 실패 ({unit_test_time:.2f}초)")
        return total_failed == 0
    
    def run_integration_tests(self):
        """통합 테스트 실행"""
        print("\n🔗 통합 테스트 실행 중...")
        
        start_time = time.time()
        
        integration_test_path = self.test_dir / "test_integration.py"
        if not integration_test_path.exists():
            print("❌ 통합 테스트 파일을 찾을 수 없습니다.")
            return False
        
        command = f"python -m pytest {integration_test_path} -v --tb=short -s"
        returncode, stdout, stderr = self.run_command(command, capture_output=False)
        
        integration_time = time.time() - start_time
        
        self.results['integration_tests'] = {
            'success': returncode == 0,
            'time': integration_time
        }
        
        if returncode == 0:
            print(f"✅ 통합 테스트 성공 ({integration_time:.2f}초)")
        else:
            print(f"❌ 통합 테스트 실패 ({integration_time:.2f}초)")
        
        return returncode == 0
    
    def run_performance_tests(self):
        """성능 테스트 실행"""
        print("\n⚡ 성능 테스트 실행 중...")
        
        start_time = time.time()
        
        # 성능 테스트 특정 항목들
        performance_commands = [
            f"python -m pytest {self.test_dir}/test_integration.py::TestCompleteWorkflow::test_large_scale_workflow -v",
            f"python -m pytest {self.test_dir}/test_integration.py::TestCompleteWorkflow::test_performance_benchmarking -v",
            f"python -m pytest {self.test_dir}/test_scheduler_engine.py::TestSchedulerEngine::test_parallel_processing_performance -v"
        ]
        
        performance_results = []
        
        for command in performance_commands:
            print(f"  🏃 {command.split('::')[-1] if '::' in command else '성능 테스트'} 실행 중...")
            returncode, stdout, stderr = self.run_command(command)
            performance_results.append(returncode == 0)
        
        performance_time = time.time() - start_time
        success_count = sum(performance_results)
        
        self.results['performance_tests'] = {
            'total': len(performance_commands),
            'passed': success_count,
            'time': performance_time
        }
        
        print(f"📊 성능 테스트 완료: {success_count}/{len(performance_commands)} 성공 ({performance_time:.2f}초)")
        return success_count == len(performance_commands)
    
    def run_coverage_analysis(self):
        """코드 커버리지 분석"""
        print("\n📈 코드 커버리지 분석 중...")
        
        # pytest-cov 설치 확인
        returncode, _, _ = self.run_command("python -c 'import pytest_cov'")
        if returncode != 0:
            print("📦 pytest-cov 설치 중...")
            self.run_command("pip install pytest-cov", capture_output=False)
        
        # 커버리지 실행
        coverage_command = (
            f"python -m pytest {self.test_dir} "
            f"--cov=core --cov=excel --cov=email --cov=gui "
            f"--cov-report=term --cov-report=html:htmlcov "
            f"--cov-fail-under=80"
        )
        
        returncode, stdout, stderr = self.run_command(coverage_command)
        
        # 커버리지 결과 파싱
        coverage_line = ""
        for line in stdout.split('\n'):
            if "TOTAL" in line and "%" in line:
                coverage_line = line
                break
        
        if coverage_line:
            coverage_percent = coverage_line.split()[-1].replace('%', '')
            print(f"📊 코드 커버리지: {coverage_percent}%")
            
            self.results['coverage'] = {
                'percentage': float(coverage_percent),
                'html_report': str(self.project_root / "htmlcov" / "index.html")
            }
        else:
            print("⚠️  커버리지 정보를 파싱할 수 없습니다.")
            self.results['coverage'] = {'percentage': 0}
        
        return returncode == 0
    
    def generate_test_report(self):
        """테스트 보고서 생성"""
        print("\n📋 테스트 보고서 생성 중...")
        
        report_path = self.project_root / "test_report.json"
        
        # 전체 결과 요약
        total_time = sum(
            result.get('time', 0) 
            for result in self.results.values() 
            if isinstance(result, dict)
        )
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_time": total_time,
            "summary": {
                "unit_tests": self.results.get('unit_tests', {}),
                "integration_tests": self.results.get('integration_tests', {}),
                "performance_tests": self.results.get('performance_tests', {}),
                "coverage": self.results.get('coverage', {})
            },
            "recommendations": self._generate_recommendations()
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📊 테스트 보고서 저장됨: {report_path}")
        self._print_summary_report(report)
        
        return report_path
    
    def _generate_recommendations(self):
        """테스트 결과 기반 권장사항 생성"""
        recommendations = []
        
        # 단위 테스트 결과 기반
        if 'unit_tests' in self.results:
            unit_results = self.results['unit_tests']
            if unit_results.get('failed', 0) > 0:
                recommendations.append("단위 테스트 실패 항목을 수정하세요.")
        
        # 커버리지 기반
        if 'coverage' in self.results:
            coverage = self.results['coverage'].get('percentage', 0)
            if coverage < 80:
                recommendations.append(f"코드 커버리지가 {coverage}%입니다. 80% 이상으로 개선을 권장합니다.")
            elif coverage >= 90:
                recommendations.append("우수한 코드 커버리지입니다!")
        
        # 성능 테스트 기반
        if 'performance_tests' in self.results:
            perf_results = self.results['performance_tests']
            if perf_results.get('passed', 0) < perf_results.get('total', 1):
                recommendations.append("성능 테스트 실패 항목을 확인하고 최적화하세요.")
        
        if not recommendations:
            recommendations.append("모든 테스트가 성공적으로 완료되었습니다! 🎉")
        
        return recommendations
    
    def _print_summary_report(self, report):
        """요약 보고서 출력"""
        print(f"\n{'='*60}")
        print(f"면접 스케줄링 시스템 테스트 요약 보고서")
        print(f"{'='*60}")
        print(f"실행 시간: {report['timestamp']}")
        print(f"총 소요 시간: {report['total_time']:.2f}초")
        print(f"")
        
        # 단위 테스트
        if 'unit_tests' in report['summary']:
            unit = report['summary']['unit_tests']
            print(f"🧪 단위 테스트:")
            print(f"   ✅ 통과: {unit.get('passed', 0)}개")
            print(f"   ❌ 실패: {unit.get('failed', 0)}개")
            print(f"   ⏱️  시간: {unit.get('time', 0):.2f}초")
        
        # 통합 테스트
        if 'integration_tests' in report['summary']:
            integration = report['summary']['integration_tests']
            status = "✅ 성공" if integration.get('success', False) else "❌ 실패"
            print(f"🔗 통합 테스트: {status} ({integration.get('time', 0):.2f}초)")
        
        # 성능 테스트
        if 'performance_tests' in report['summary']:
            perf = report['summary']['performance_tests']
            print(f"⚡ 성능 테스트: {perf.get('passed', 0)}/{perf.get('total', 0)} 성공 ({perf.get('time', 0):.2f}초)")
        
        # 코드 커버리지
        if 'coverage' in report['summary']:
            coverage = report['summary']['coverage']
            print(f"📈 코드 커버리지: {coverage.get('percentage', 0)}%")
            if 'html_report' in coverage:
                print(f"   📊 상세 보고서: {coverage['html_report']}")
        
        print(f"\n💡 권장사항:")
        for rec in report['recommendations']:
            print(f"   • {rec}")
        
        print(f"{'='*60}")
    
    def main(self, args):
        """메인 실행 함수"""
        print("🚀 면접 스케줄링 시스템 테스트 실행기")
        print(f"📁 프로젝트 경로: {self.project_root}")
        
        start_time = time.time()
        
        # 의존성 확인
        self.check_dependencies()
        
        success = True
        
        # 테스트 실행
        if args.integration:
            success &= self.run_integration_tests()
        elif args.performance:
            success &= self.run_performance_tests()
        elif args.fast:
            # 빠른 테스트만 (단위 테스트 일부)
            print("\n⚡ 빠른 테스트 모드")
            success &= self.run_unit_tests()
        else:
            # 전체 테스트 실행
            success &= self.run_unit_tests()
            success &= self.run_integration_tests()
            
            if not args.skip_performance:
                success &= self.run_performance_tests()
            
            if args.coverage:
                self.run_coverage_analysis()
        
        # 보고서 생성
        report_path = self.generate_test_report()
        
        total_time = time.time() - start_time
        
        if success:
            print(f"\n🎉 모든 테스트가 성공적으로 완료되었습니다! (총 {total_time:.2f}초)")
            print(f"🚀 시스템이 프로덕션 배포 준비 상태입니다.")
        else:
            print(f"\n❌ 일부 테스트가 실패했습니다. (총 {total_time:.2f}초)")
            print(f"🔧 실패한 테스트를 수정 후 다시 실행해주세요.")
        
        return 0 if success else 1


def main():
    """명령행 인터페이스"""
    parser = argparse.ArgumentParser(
        description="면접 스케줄링 시스템 종합 테스트 실행기",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--fast",
        action="store_true",
        help="빠른 테스트만 실행 (단위 테스트)"
    )
    
    parser.add_argument(
        "--integration",
        action="store_true", 
        help="통합 테스트만 실행"
    )
    
    parser.add_argument(
        "--performance",
        action="store_true",
        help="성능 테스트만 실행"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="코드 커버리지 분석 포함"
    )
    
    parser.add_argument(
        "--skip-performance",
        action="store_true",
        help="성능 테스트 건너뛰기"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    return runner.main(args)


if __name__ == "__main__":
    sys.exit(main())