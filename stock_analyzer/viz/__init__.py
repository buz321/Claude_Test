"""시각화: matplotlib 기반 차트.

matplotlib가 설치되지 않은 환경에서도 패키지 임포트가 깨지지 않도록
charts 모듈은 사용 시점에 임포트한다.
"""

from .charts import plot_analysis

__all__ = ["plot_analysis"]
