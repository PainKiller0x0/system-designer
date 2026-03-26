#!/usr/bin/env python3
"""
系统策划多智能体框架 - 统一入口

用法:
  python run.py --agent <name> --input '<json>' [--session-id <timestamp>]
  python run.py --agent <name> --input @path/to/input.json [--session-id <timestamp>]

可用 Agent:
  requirements_analyzer  需求拆解（分析 UI 参考图，输出需求 Draft）
  system_designer        系统策划（根据需求 Draft 撰写策划案）
  standards_reviewer     规范审查（检查策划案是否符合标准规范）
  prompt_guardian        Prompt 守护（分析对话记录，建议原子级 prompt 更新）
"""

import argparse
import json
import sys
import logging
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from tools.save_conversation import save_test_io


# 配置日志
def setup_logging():
    """配置日志系统"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    verbose = os.getenv("VERBOSE_LOGGING", "false").lower() == "true"
    
    # 创建日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if verbose:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    
    # 配置根日志记录器
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stderr),  # 输出到 stderr
        ]
    )
    
    return logging.getLogger(__name__)


# 初始化日志
logger = setup_logging()


class AgentError(Exception):
    """Agent 执行错误"""
    pass


class InputValidationError(Exception):
    """输入验证错误"""
    pass


def validate_input(input_data: dict, agent_name: str) -> None:
    """验证输入数据的有效性"""
    if not isinstance(input_data, dict):
        raise InputValidationError(f"输入必须是字典类型，收到: {type(input_data)}")
    
    # 根据 agent 类型验证必要字段
    required_fields = {
        "requirements_analyzer": ["image_path", "user_input"],
        "system_designer": ["requirements_draft"],
        "standards_reviewer": ["planning_document"],
        "prompt_guardian": ["conversation_summary"],
    }
    
    if agent_name in required_fields:
        for field in required_fields[agent_name]:
            if field not in input_data:
                logger.warning(f"Agent '{agent_name}' 缺少推荐字段: {field}")


def run_agent(agent_name: str, input_data: dict) -> dict:
    """执行 Agent 并处理异常"""
    try:
        logger.info(f"开始执行 Agent: {agent_name}")
        
        # 路由到对应 Agent
        agent_map = {
            "requirements_analyzer": "agents.requirements_analyzer",
            "system_designer": "agents.system_designer",
            "standards_reviewer": "agents.standards_reviewer",
            "prompt_guardian": "agents.prompt_guardian",
        }
        
        if agent_name not in agent_map:
            raise AgentError(f"未知的 Agent: {agent_name}")
        
        import importlib
        module = importlib.import_module(agent_map[agent_name])
        result = module.run(input_data)
        
        logger.info(f"Agent '{agent_name}' 执行成功")
        return result
        
    except ImportError as e:
        logger.error(f"导入 Agent 模块失败: {e}")
        raise AgentError(f"无法加载 Agent '{agent_name}': {e}")
    except Exception as e:
        logger.error(f"Agent '{agent_name}' 执行失败: {e}", exc_info=True)
        raise


def main():
    parser = argparse.ArgumentParser(
        description="系统策划多智能体框架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py --agent requirements_analyzer --input '{"image_path": "ref.png", "user_input": "设计一个签到系统"}'
  python run.py --agent system_designer --input @input.json --session-id 20240101_120000
        """
    )
    parser.add_argument(
        "--agent",
        required=True,
        choices=["requirements_analyzer", "system_designer", "standards_reviewer", "prompt_guardian"],
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
        
        # 保存入参到 data/test/
        save_test_io(args.agent, input_data, timestamp=session_id)
        
        # 执行 Agent
        result = run_agent(args.agent, input_data)
        
        # 保存出参到 data/test/
        save_test_io(args.agent, input_data, result, timestamp=session_id)
        
        # 打印结果到 stdout（JSON 格式，用于程序解析）
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 打印 token 消耗到 stderr（用户可见，不影响 JSON 解析）
        if "usage" in result:
            usage = result["usage"]
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = input_tokens + output_tokens
            print(f"\n📊 Token 消耗统计：输入 {input_tokens} | 输出 {output_tokens} | 总计 {total_tokens}", file=sys.stderr)
        
        logger.info(f"Session {session_id} 执行完成")
        
    except InputValidationError as e:
        logger.error(f"输入验证失败: {e}")
        print(json.dumps({"error": f"输入验证失败: {e}"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    except AgentError as e:
        logger.error(f"Agent 执行失败: {e}")
        print(json.dumps({"error": f"Agent 执行失败: {e}"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
        print(json.dumps({"error": f"文件未找到: {e}"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
        print(json.dumps({"error": f"JSON 解析失败: {e}"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"未知错误: {e}", exc_info=True)
        print(json.dumps({"error": f"未知错误: {e}"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
