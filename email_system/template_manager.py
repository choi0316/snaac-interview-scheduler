"""
이메일 템플릿 관리 시스템

다양한 상황별 이메일 템플릿을 관리하고 개인화된 메일 콘텐츠를 생성합니다.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """템플릿 유형"""
    INTERVIEW_NOTIFICATION = "interview_notification"
    REJECTION_NOTIFICATION = "rejection_notification" 
    REMINDER = "reminder"
    CONFIRMATION = "confirmation"
    SCHEDULE_CHANGE = "schedule_change"
    FOLLOW_UP = "follow_up"


class EmailUrgency(Enum):
    """이메일 긴급도"""
    LOW = "낮음"
    NORMAL = "보통"
    HIGH = "높음"
    URGENT = "긴급"


@dataclass
class EmailTemplate:
    """이메일 템플릿"""
    template_id: str
    template_type: TemplateType
    name: str
    subject_template: str
    body_template: str
    variables: List[str]
    language: str = "ko"
    urgency: EmailUrgency = EmailUrgency.NORMAL
    
    # 메타데이터
    created_at: datetime = None
    updated_at: datetime = None
    version: str = "1.0"
    description: str = ""
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class EmailContent:
    """생성된 이메일 콘텐츠"""
    recipient: str
    subject: str
    body: str
    template_id: str
    urgency: EmailUrgency
    variables_used: Dict[str, Any]
    generated_at: datetime = None
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now()


class EmailTemplateManager:
    """이메일 템플릿 관리자"""
    
    def __init__(self, templates_dir: Optional[str] = None):
        self.templates: Dict[str, EmailTemplate] = {}
        self.templates_dir = Path(templates_dir) if templates_dir else None
        
        # 기본 템플릿 변수
        self.global_variables = {
            '{{organization}}': '공모전 운영사무국',
            '{{contact_email}}': 'admin@contest.org',
            '{{contact_phone}}': '02-1234-5678',
            '{{website}}': 'https://contest.org',
            '{{current_date}}': datetime.now().strftime('%Y년 %m월 %d일'),
            '{{current_year}}': str(datetime.now().year)
        }
        
        # 조건부 블록 패턴
        self.conditional_pattern = re.compile(
            r'\{\{#if_([\w]+)\}\}(.*?)\{\{/if_\1\}\}',
            re.DOTALL
        )
        
        # 반복 블록 패턴
        self.loop_pattern = re.compile(
            r'\{\{#each_([\w]+)\}\}(.*?)\{\{/each_\1\}\}',
            re.DOTALL
        )
        
        # 기본 템플릿 로드
        self._load_default_templates()
        
        # 외부 템플릿 파일 로드
        if self.templates_dir and self.templates_dir.exists():
            self._load_external_templates()
    
    def _load_default_templates(self):
        """기본 템플릿 로드"""
        
        # 합격자 면접 안내 템플릿
        interview_template = EmailTemplate(
            template_id="interview_notification",
            template_type=TemplateType.INTERVIEW_NOTIFICATION,
            name="면접 안내 메일",
            subject_template="[{{organization}}] {{team_name}} 팀 2차 면접 안내",
            body_template="""안녕하세요, {{leader_name}}님.

{{team_name}} 팀의 2차 면접 일정을 안내드립니다.

📅 면접 일정 정보
• 면접 날짜: {{interview_date}}
• 면접 시간: {{interview_time}}
• 면접 조: {{interview_group}}
• 면접 장소: {{interview_room}}
{{#if_online}}
• 온라인 링크: {{zoom_link}}
{{/if_online}}

📋 면접 준비사항
• 발표자료: 10분 이내 프레젠테이션
• 질의응답: 5분
• 지참물: 신분증, 팀원 전원 참석

{{#if_additional_info}}
📌 추가 안내사항
{{additional_info}}
{{/if_additional_info}}

면접 관련 문의사항이 있으시면 언제든 연락 주세요.

감사합니다.

{{organization}}
연락처: {{contact_email}} / {{contact_phone}}
""",
            variables=[
                'team_name', 'leader_name', 'interview_date', 'interview_time',
                'interview_group', 'interview_room', 'zoom_link', 'additional_info'
            ],
            urgency=EmailUrgency.HIGH,
            description="합격자에게 발송하는 면접 일정 안내 메일"
        )
        
        # 탈락자 안내 템플릿
        rejection_template = EmailTemplate(
            template_id="rejection_notification", 
            template_type=TemplateType.REJECTION_NOTIFICATION,
            name="탈락 안내 메일",
            subject_template="[{{organization}}] 심사 결과 안내",
            body_template="""안녕하세요, {{leader_name}}님.

{{team_name}} 팀의 공모전 참가에 진심으로 감사드립니다.

많은 우수한 팀들이 지원하여 치열한 경쟁을 펼쳤으며,
아쉽게도 2차 면접 대상에서 제외되었음을 안내드립니다.

이번 기회를 통해 보여주신 아이디어와 열정에 깊이 감사드리며,
앞으로도 더 많은 좋은 기회로 만나뵐 수 있기를 바랍니다.

{{#if_feedback}}
📌 심사위원 피드백
{{feedback}}
{{/if_feedback}}

감사합니다.

{{organization}}
연락처: {{contact_email}}
""",
            variables=['team_name', 'leader_name', 'feedback'],
            urgency=EmailUrgency.NORMAL,
            description="탈락자에게 발송하는 결과 안내 메일"
        )
        
        # 면접 리마인더 템플릿
        reminder_template = EmailTemplate(
            template_id="interview_reminder",
            template_type=TemplateType.REMINDER,
            name="면접 리마인더",
            subject_template="[{{organization}}] 내일 면접 일정 리마인더",
            body_template="""안녕하세요, {{leader_name}}님.

내일 예정된 {{team_name}} 팀의 면접 일정을 리마인드드립니다.

📅 면접 일정
• 날짜: {{interview_date}}
• 시간: {{interview_time}}
• 장소: {{interview_room}}
{{#if_online}}
• 온라인 링크: {{zoom_link}}
{{/if_online}}

📋 체크리스트
• 발표자료 준비 완료
• 팀원 전원 참석 확인
• 신분증 지참
• 10분 전 도착

좋은 결과 있으시길 바랍니다.

감사합니다.

{{organization}}
""",
            variables=[
                'team_name', 'leader_name', 'interview_date', 
                'interview_time', 'interview_room', 'zoom_link'
            ],
            urgency=EmailUrgency.HIGH,
            description="면접 전날 발송하는 리마인더 메일"
        )
        
        # 일정 변경 템플릿
        schedule_change_template = EmailTemplate(
            template_id="schedule_change",
            template_type=TemplateType.SCHEDULE_CHANGE,
            name="일정 변경 안내",
            subject_template="[{{organization}}] {{team_name}} 팀 면접 일정 변경 안내",
            body_template="""안녕하세요, {{leader_name}}님.

{{team_name}} 팀의 면접 일정이 변경되었음을 안내드립니다.

📅 변경된 면접 일정
• 기존 일정: {{original_date}} {{original_time}}
• 변경 일정: {{new_date}} {{new_time}}
• 면접 장소: {{interview_room}}
{{#if_online}}
• 온라인 링크: {{zoom_link}}
{{/if_online}}

📌 변경 사유
{{change_reason}}

갑작스러운 일정 변경으로 불편을 드려 죄송합니다.
변경된 일정으로 참석 부탁드립니다.

감사합니다.

{{organization}}
연락처: {{contact_email}} / {{contact_phone}}
""",
            variables=[
                'team_name', 'leader_name', 'original_date', 'original_time',
                'new_date', 'new_time', 'interview_room', 'zoom_link', 'change_reason'
            ],
            urgency=EmailUrgency.URGENT,
            description="면접 일정 변경시 발송하는 긴급 안내 메일"
        )
        
        # 확인 템플릿
        confirmation_template = EmailTemplate(
            template_id="interview_confirmation",
            template_type=TemplateType.CONFIRMATION,
            name="면접 참석 확인",
            subject_template="[{{organization}}] {{team_name}} 팀 면접 참석 확인 요청",
            body_template="""안녕하세요, {{leader_name}}님.

{{team_name}} 팀의 면접 참석 확인을 요청드립니다.

📅 면접 일정
• 날짜: {{interview_date}}
• 시간: {{interview_time}}
• 장소: {{interview_room}}

다음 링크를 통해 참석 여부를 확인해주세요:
{{confirmation_link}}

{{confirmation_deadline}}까지 확인 부탁드립니다.

감사합니다.

{{organization}}
""",
            variables=[
                'team_name', 'leader_name', 'interview_date',
                'interview_time', 'interview_room', 'confirmation_link',
                'confirmation_deadline'
            ],
            urgency=EmailUrgency.NORMAL,
            description="면접 참석 확인을 요청하는 메일"
        )
        
        # 템플릿 등록
        templates = [
            interview_template, rejection_template, reminder_template,
            schedule_change_template, confirmation_template
        ]
        
        for template in templates:
            self.templates[template.template_id] = template
        
        logger.info(f"기본 템플릿 {len(templates)}개 로드 완료")
    
    def _load_external_templates(self):
        """외부 템플릿 파일 로드"""
        
        try:
            template_files = list(self.templates_dir.glob("*.json"))
            
            for file_path in template_files:
                with open(file_path, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                template = EmailTemplate(
                    template_id=template_data['template_id'],
                    template_type=TemplateType(template_data['template_type']),
                    name=template_data['name'],
                    subject_template=template_data['subject_template'],
                    body_template=template_data['body_template'],
                    variables=template_data['variables'],
                    language=template_data.get('language', 'ko'),
                    urgency=EmailUrgency(template_data.get('urgency', 'NORMAL')),
                    description=template_data.get('description', '')
                )
                
                self.templates[template.template_id] = template
                logger.info(f"외부 템플릿 로드: {template.name}")
                
        except Exception as e:
            logger.error(f"외부 템플릿 로드 오류: {e}")
    
    def generate_email_content(
        self,
        template_id: str,
        recipient: str,
        variables: Dict[str, Any],
        override_global: bool = False
    ) -> Optional[EmailContent]:
        """개인화된 이메일 콘텐츠 생성"""
        
        if template_id not in self.templates:
            logger.error(f"템플릿을 찾을 수 없음: {template_id}")
            return None
        
        template = self.templates[template_id]
        
        try:
            # 변수 병합 (글로벌 + 개인화)
            all_variables = self.global_variables.copy()
            if not override_global:
                all_variables.update(variables)
            else:
                all_variables = variables
            
            # 제목 생성
            subject = self._render_template(template.subject_template, all_variables)
            
            # 본문 생성
            body = self._render_template(template.body_template, all_variables)
            
            # 조건부 블록 처리
            body = self._process_conditional_blocks(body, all_variables)
            
            # 반복 블록 처리
            body = self._process_loop_blocks(body, all_variables)
            
            # 최종 정리
            body = self._clean_template_output(body)
            
            email_content = EmailContent(
                recipient=recipient,
                subject=subject,
                body=body,
                template_id=template_id,
                urgency=template.urgency,
                variables_used=all_variables
            )
            
            logger.debug(f"이메일 콘텐츠 생성 완료: {recipient}")
            return email_content
            
        except Exception as e:
            logger.error(f"이메일 콘텐츠 생성 오류 {template_id}: {e}")
            return None
    
    def _render_template(self, template_str: str, variables: Dict[str, Any]) -> str:
        """템플릿 렌더링"""
        
        rendered = template_str
        
        for var_name, var_value in variables.items():
            if var_value is not None:
                # 문자열 변환 및 이스케이프 처리
                str_value = str(var_value).strip()
                rendered = rendered.replace(var_name, str_value)
        
        return rendered
    
    def _process_conditional_blocks(self, content: str, variables: Dict[str, Any]) -> str:
        """조건부 블록 처리"""
        
        def replace_conditional(match):
            condition_name = match.group(1)
            block_content = match.group(2)
            
            # 조건 변수 확인
            condition_var = f"{{{{{condition_name}}}}}"
            condition_value = variables.get(condition_var)
            
            # 조건 평가
            if self._evaluate_condition(condition_value):
                return block_content
            else:
                return ""
        
        return self.conditional_pattern.sub(replace_conditional, content)
    
    def _process_loop_blocks(self, content: str, variables: Dict[str, Any]) -> str:
        """반복 블록 처리"""
        
        def replace_loop(match):
            loop_name = match.group(1)
            block_content = match.group(2)
            
            # 반복 데이터 확인
            loop_var = f"{{{{{loop_name}}}}}"
            loop_data = variables.get(loop_var)
            
            if not isinstance(loop_data, list):
                return ""
            
            # 반복 렌더링
            rendered_blocks = []
            for item in loop_data:
                if isinstance(item, dict):
                    item_content = block_content
                    for key, value in item.items():
                        item_content = item_content.replace(f"{{{{{key}}}}}", str(value))
                    rendered_blocks.append(item_content)
                else:
                    item_content = block_content.replace("{{item}}", str(item))
                    rendered_blocks.append(item_content)
            
            return "\n".join(rendered_blocks)
        
        return self.loop_pattern.sub(replace_loop, content)
    
    def _evaluate_condition(self, value: Any) -> bool:
        """조건 평가"""
        
        if value is None:
            return False
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return len(value.strip()) > 0
        
        if isinstance(value, (int, float)):
            return value != 0
        
        if isinstance(value, (list, dict)):
            return len(value) > 0
        
        return bool(value)
    
    def _clean_template_output(self, content: str) -> str:
        """템플릿 출력 정리"""
        
        # 빈 줄 정리
        lines = content.split('\n')
        cleaned_lines = []
        
        prev_empty = False
        for line in lines:
            is_empty = len(line.strip()) == 0
            
            if not (is_empty and prev_empty):  # 연속 빈줄 방지
                cleaned_lines.append(line)
            
            prev_empty = is_empty
        
        # 앞뒤 빈 줄 제거
        content = '\n'.join(cleaned_lines).strip()
        
        # 남은 템플릿 변수 처리 (값이 없는 경우)
        content = re.sub(r'\{\{[^}]+\}\}', '', content)
        
        return content
    
    def batch_generate_emails(
        self,
        template_id: str,
        recipients_data: List[Dict[str, Any]]
    ) -> List[EmailContent]:
        """일괄 이메일 생성"""
        
        email_contents = []
        
        for recipient_data in recipients_data:
            recipient_email = recipient_data.get('email', '')
            if not recipient_email:
                logger.warning("수신자 이메일 누락")
                continue
            
            variables = {k: v for k, v in recipient_data.items() if k != 'email'}
            
            # 변수명을 템플릿 형식으로 변환
            template_variables = {f"{{{{{k}}}}}": v for k, v in variables.items()}
            
            content = self.generate_email_content(
                template_id, recipient_email, template_variables
            )
            
            if content:
                email_contents.append(content)
        
        logger.info(f"일괄 이메일 생성 완료: {len(email_contents)}개")
        return email_contents
    
    def schedule_reminder_emails(
        self,
        schedules: List[Dict],
        reminder_hours: int = 24
    ) -> List[EmailContent]:
        """리마인더 이메일 예약"""
        
        reminder_emails = []
        template_id = "interview_reminder"
        
        for schedule in schedules:
            # 면접 시간 파싱
            try:
                interview_datetime = datetime.strptime(
                    f"{schedule['interview_date']} {schedule['interview_time'][:5]}", 
                    "%Y-%m-%d %H:%M"
                )
                
                reminder_time = interview_datetime - timedelta(hours=reminder_hours)
                
                # 현재 시간보다 미래인 경우만 처리
                if reminder_time > datetime.now():
                    variables = {
                        '{{team_name}}': schedule.get('team_name', ''),
                        '{{leader_name}}': schedule.get('leader_name', ''),
                        '{{interview_date}}': schedule.get('interview_date', ''),
                        '{{interview_time}}': schedule.get('interview_time', ''),
                        '{{interview_room}}': schedule.get('interview_room', ''),
                        '{{zoom_link}}': schedule.get('zoom_link', ''),
                    }
                    
                    content = self.generate_email_content(
                        template_id, schedule.get('email', ''), variables
                    )
                    
                    if content:
                        # 발송 시간 정보 추가
                        content.scheduled_time = reminder_time
                        reminder_emails.append(content)
                        
            except Exception as e:
                logger.error(f"리마인더 스케줄링 오류: {e}")
                continue
        
        logger.info(f"리마인더 이메일 {len(reminder_emails)}개 예약")
        return reminder_emails
    
    def add_custom_template(self, template: EmailTemplate) -> bool:
        """사용자 정의 템플릿 추가"""
        
        try:
            # 템플릿 검증
            if not self._validate_template(template):
                return False
            
            self.templates[template.template_id] = template
            
            # 파일로 저장 (설정된 경우)
            if self.templates_dir:
                self._save_template_to_file(template)
            
            logger.info(f"사용자 정의 템플릿 추가: {template.name}")
            return True
            
        except Exception as e:
            logger.error(f"템플릿 추가 오류: {e}")
            return False
    
    def _validate_template(self, template: EmailTemplate) -> bool:
        """템플릿 유효성 검사"""
        
        if not template.template_id:
            logger.error("템플릿 ID가 없습니다")
            return False
        
        if not template.subject_template or not template.body_template:
            logger.error("제목 또는 본문 템플릿이 없습니다")
            return False
        
        # 변수 일관성 검사
        subject_vars = re.findall(r'\{\{([^}]+)\}\}', template.subject_template)
        body_vars = re.findall(r'\{\{([^}]+)\}\}', template.body_template)
        all_template_vars = set(subject_vars + body_vars)
        
        declared_vars = set(template.variables)
        
        # 선언되지 않은 변수가 있는지 확인
        undeclared_vars = all_template_vars - declared_vars - set(self.global_variables.keys())
        if undeclared_vars:
            logger.warning(f"선언되지 않은 변수: {undeclared_vars}")
        
        return True
    
    def _save_template_to_file(self, template: EmailTemplate):
        """템플릿을 파일로 저장"""
        
        template_data = {
            'template_id': template.template_id,
            'template_type': template.template_type.value,
            'name': template.name,
            'subject_template': template.subject_template,
            'body_template': template.body_template,
            'variables': template.variables,
            'language': template.language,
            'urgency': template.urgency.value,
            'description': template.description,
            'version': template.version
        }
        
        file_path = self.templates_dir / f"{template.template_id}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2)
    
    def get_template_list(self) -> List[Dict[str, Any]]:
        """템플릿 목록 조회"""
        
        template_list = []
        
        for template in self.templates.values():
            template_info = {
                'template_id': template.template_id,
                'name': template.name,
                'type': template.template_type.value,
                'urgency': template.urgency.value,
                'variables_count': len(template.variables),
                'description': template.description,
                'created_at': template.created_at.isoformat() if template.created_at else None
            }
            template_list.append(template_info)
        
        # 생성일 기준 정렬
        template_list.sort(key=lambda x: x['created_at'] or '', reverse=True)
        
        return template_list
    
    def get_template_preview(self, template_id: str, sample_data: Dict[str, Any] = None) -> Optional[Dict[str, str]]:
        """템플릿 미리보기"""
        
        if template_id not in self.templates:
            return None
        
        template = self.templates[template_id]
        
        # 샘플 데이터 설정
        if sample_data is None:
            sample_data = {
                '{{team_name}}': '샘플팀',
                '{{leader_name}}': '홍길동',
                '{{interview_date}}': '2024-01-15',
                '{{interview_time}}': '14:00-14:30',
                '{{interview_group}}': 'A조',
                '{{interview_room}}': 'A조 면접실',
                '{{zoom_link}}': 'https://zoom.us/j/1234567890',
                '{{additional_info}}': '추가 준비물: 노트북'
            }
        
        # 미리보기 생성
        preview_content = self.generate_email_content(
            template_id, 'sample@example.com', sample_data
        )
        
        if preview_content:
            return {
                'subject': preview_content.subject,
                'body': preview_content.body,
                'urgency': preview_content.urgency.value
            }
        
        return None
    
    def export_templates(self, output_path: str) -> bool:
        """템플릿을 파일로 내보내기"""
        
        try:
            export_data = []
            
            for template in self.templates.values():
                template_data = {
                    'template_id': template.template_id,
                    'template_type': template.template_type.value,
                    'name': template.name,
                    'subject_template': template.subject_template,
                    'body_template': template.body_template,
                    'variables': template.variables,
                    'language': template.language,
                    'urgency': template.urgency.value,
                    'description': template.description,
                    'version': template.version,
                    'created_at': template.created_at.isoformat() if template.created_at else None
                }
                export_data.append(template_data)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"템플릿 내보내기 완료: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"템플릿 내보내기 오류: {e}")
            return False
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """템플릿 사용 통계"""
        
        stats = {
            'total_templates': len(self.templates),
            'templates_by_type': {},
            'templates_by_urgency': {},
            'average_variables_per_template': 0
        }
        
        total_variables = 0
        
        for template in self.templates.values():
            # 유형별 통계
            type_name = template.template_type.value
            stats['templates_by_type'][type_name] = stats['templates_by_type'].get(type_name, 0) + 1
            
            # 긴급도별 통계
            urgency_name = template.urgency.value
            stats['templates_by_urgency'][urgency_name] = stats['templates_by_urgency'].get(urgency_name, 0) + 1
            
            # 변수 수 통계
            total_variables += len(template.variables)
        
        if len(self.templates) > 0:
            stats['average_variables_per_template'] = total_variables / len(self.templates)
        
        return stats