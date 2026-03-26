#!/usr/bin/env python3
"""
OpenCode 适配器 - 让 OpenCode 能够调用 System Designer 的 Agent

用法:
  python opencode_adapter.py --agent <name> --input '<json>' [--session-id <timestamp>]

支持的 Agent:
  requirements_analyzer  需求拆解
  system_designer        系统策划
  standards_reviewer     规范审查
  prompt_guardian        Prompt 守护
  reverse_requirements   逆向需求

与 run.py 的区别:
  - run.py: 用于调试单个 Agent
  - opencode_adapter.py: 为 OpenCode 提供统一接口，包含额外的 OpenCode 特定处理
"""

import argparse
import json
import sys
import logging
import os
from pathlib import Path
from datetime import datetime

# 设置路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "subagent" / "system_designer_beta"))

from dotenv import load_dotenv
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)


def validate_input(input_data: dict, agent_name: str) -> None:
    """验证输入数据的有效性"""
    if not isinstance(input_data, dict):
        raise ValueError(f"输入必须是字典类型，收到: {type(input_data)}")
    
    # 根据 agent 类型验证必要字段
    required_fields = {
        "requirements_analyzer": ["image_path", "user_input"],
        "system_designer": ["requirements_draft"],
        "standards_reviewer": ["planning_document"],
        "prompt_guardian": ["conversation_summary"],
        "reverse_requirements": ["planning_document"],
    }
    
    if agent_name in required_fields:
        for field in required_fields[agent_name]:
            if field not in input_data:
                logger.warning(f"Agent '{agent_name}' 缺少推荐字段: {field}")


def run_agent(agent_name: str, input_data: dict) -> dict:
    """执行 Agent"""
    # 路由到对应 Agent
    agent_map = {
        "requirements_analyzer": "agents.requirements_analyzer",
        "system_designer": "agents.system_designer",
        "standards_reviewer": "agents.standards_reviewer",
        "prompt_guardian": "agents.prompt_guardian",
    }
    
    if agent_name not in agent_map:
        raise ValueError(f"未知的 Agent: {agent_name}")
    
    import importlib
    module = importlib.import_module(agent_map[agent_name])
    return module.run(input_data)


def main():
    parser = argparse.ArgumentParser(
        description="OpenCode 适配器 - System Designer Agent 调用接口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python opencode_adapter.py --agent requirements_analyzer --input '{"image_path": "ref.png", "user_input": "设计一个签到系统"}'
  python opencode_adapter.py --agent system_designer --input @input.json --session-id 20240101_120000
        """
    )
    parser.add_argument(
        "--agent",
        required=True,
        choices=["requirements_analyzer", "system_designer", "standards_reviewer", "prompt_guardian", "reverse_requirements"],
        help="要调用的 Agent 名称",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="JSON 输入字符串，或以 @ 开头的文件路径（如 @input.json）",
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="会话时间戳，用于日志文件命名（默认自动生成）",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="启用详细日志输出",
    )
    args = parser.parse_args()
    
    # 设置详细日志
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("已启用详细日志模式")
    
    session_id = args.session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Agent: {args.agent}")
    
    try:
        # 加载输入
        if args.input.startswith("@"):
            input_file = args.input[1:]
            logger.debug(f"从文件加载输入: {input_file}")
            with open(input_file, encoding="utf-8") as f:
                input_data = json.load(f)
        else:
            input_data = json.loads(args.input)
        
        # 验证输入
        validate_input(input_data, args.agent)
        
        # 执行 Agent
        result = run_agent(args.agent, input_data)
        
        # 打印结果到 stdout（JSON 格式，用于程序解析）
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 打印 token 消耗到 stderr
        if "usage" in result:
            usage = result["usage"]
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = input_tokens + output_tokens
            print(f"\n📊 Token 消耗统计：输入 {input_tokens} | 输出 {output_tokens} | 总计 {total_tokens}", file=sys.stderr)
        
        logger.info(f"Session {session_id} 执行完成")
        
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
        print(json.dumps({"error": f"文件未找到: {e}"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
        print(json.dumps({"error": f"JSON 解析失败: {e}"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        print(json.dumps({"error": f"执行失败: {e}"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()