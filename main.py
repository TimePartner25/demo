"""
DEMO 主程序
"""

import asyncio
import sys
from queue import Queue
from typing import Optional

from src.config import API_KEY, API_BASE_URL, BATCH_SIZE, MAX_RECENT_DIALOGUE
from src.api import initialize_api_client
from src.storage import PersonaManager
from src.agents import InterviewAgent, ProcessingAgent, StyleSummaryAgent, ImpersonationAgent
from src.models import KnowledgeBase, StyleBase, OralHabitsBase


class REDemo:
    """主应用类"""
    
    def __init__(self):
        self.persona_manager = PersonaManager()
        self.current_persona = None
        self.persona_data = None
        
        # 初始化API客户端
        initialize_api_client(API_KEY, API_BASE_URL)
    
    def show_menu(self):
        """显示主菜单"""
        print("\n" + "="*50)
        print("RE-DEMO - 多智能体角色扮演系统")
        print("="*50)
        print("\n请选择操作：")
        print("1. 加载已有人物知识库")
        print("2. 创建新人物知识库")
        print("3. 管理知识库（查看/删除）")
        print("4. 退出")
        print()
    
    def list_personas_menu(self):
        """列出所有人物"""
        personas = self.persona_manager.list_personas()
        
        if not personas:
            print("\n当前没有已存在的人物知识库。")
            return None
        
        print("\n已存在的人物知识库：")
        for i, name in enumerate(personas, 1):
            stats = self.persona_manager.get_persona_stats(name)
            if stats:
                print(f"{i}. {name} - 事实:{stats['facts_count']} 风格:{stats['style_observations']} 对话:{stats['history_length']}")
            else:
                print(f"{i}. {name}")
        
        print("0. 返回")
        
        choice = input("\n请选择人物编号: ").strip()
        
        if choice == "0":
            return None
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(personas):
                return personas[idx]
        except ValueError:
            pass
        
        print("无效选择")
        return None
    
    def load_persona(self):
        """加载人物"""
        persona_name = self.list_personas_menu()
        
        if persona_name:
            self.persona_data = self.persona_manager.load_persona(persona_name)
            self.current_persona = persona_name
            print(f"\n✓ 成功加载人物: {persona_name}")
            return True
        
        return False
    
    def create_new_persona(self):
        """创建新人物"""
        print("\n创建新人物知识库")
        persona_name = input("请输入人物名称: ").strip()
        
        if not persona_name:
            print("人物名称不能为空")
            return False
        
        if self.persona_manager.persona_exists(persona_name):
            print(f"人物 '{persona_name}' 已存在")
            return False
        
        self.persona_data = self.persona_manager.create_new_persona(persona_name)
        self.current_persona = persona_name
        print(f"\n✓ 成功创建人物: {persona_name}")
        return True
    
    def manage_personas(self):
        """管理人物知识库"""
        while True:
            print("\n知识库管理")
            print("1. 查看人物详情")
            print("2. 删除人物")
            print("0. 返回")
            
            choice = input("\n请选择: ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self.view_persona_details()
            elif choice == "2":
                self.delete_persona()
    
    def view_persona_details(self):
        """查看人物详情"""
        persona_name = self.list_personas_menu()
        
        if persona_name:
            stats = self.persona_manager.get_persona_stats(persona_name)
            if stats:
                print(f"\n人物: {stats['name']}")
                print(f"事实数量: {stats['facts_count']}")
                print(f"风格观察: {stats['style_observations']}")
                print(f"语言习惯: {stats['oral_habits']}")
                print(f"对话历史: {stats['history_length']} 条")
    
    def delete_persona(self):
        """删除人物"""
        persona_name = self.list_personas_menu()
        
        if persona_name:
            confirm = input(f"\n⚠️  确定要删除 '{persona_name}' 吗？此操作不可撤销！(yes/no): ").strip().lower()
            
            if confirm == "yes":
                if self.persona_manager.delete_persona(persona_name):
                    print(f"✓ 已删除人物: {persona_name}")
                else:
                    print("删除失败")
    
    def show_mode_menu(self):
        """显示模式选择菜单"""
        print(f"\n当前人物: {self.current_persona}")
        print("\n请选择模式：")
        print("1. 采访模式 - 采集人物信息")
        print("2. 扮演模式 - 模拟人物对话")
        print("0. 返回主菜单")
        print()
    
    async def interview_mode(self):
        """采访模式"""
        print("\n" + "="*50)
        print(f"采访模式 - {self.current_persona}")
        print("="*50)
        print("提示: 输入 'quit' 退出采访模式\n")
        
        # 初始化队列和智能体
        qa_fact_queue = Queue()
        qa_style_queue = Queue()
        
        # 创建智能体
        interview_agent = InterviewAgent(
            knowledge_base=self.persona_data["knowledge_base"],
            qa_fact_cache_queue=qa_fact_queue,
            qa_style_cache_queue=qa_style_queue,
            history=self.persona_data["history"],
            max_recent_dialogue=MAX_RECENT_DIALOGUE
        )
        
        processing_agent = ProcessingAgent(
            knowledge_base=self.persona_data["knowledge_base"],
            qa_fact_cache_queue=qa_fact_queue,
            batch_size=BATCH_SIZE
        )
        
        style_agent = StyleSummaryAgent(
            style_base=self.persona_data["style_base"],
            oral_habits_base=self.persona_data["oral_habits_base"],
            qa_style_cache_queue=qa_style_queue,
            batch_size=BATCH_SIZE
        )
        
        # 启动后台智能体
        processing_task = asyncio.create_task(processing_agent.run())
        style_task = asyncio.create_task(style_agent.run())
        
        try:
            # 开始采访
            print("AI: ", end="")
            first_question = await interview_agent.start_interview()
            
            # 对话循环
            while True:
                user_input = input("\n你: ").strip()
                
                if user_input.lower() == 'quit':
                    print("\n正在退出采访模式...")
                    break
                
                if not user_input:
                    continue
                
                print("\nAI: ", end="")
                await interview_agent.process_chat(user_input)
        
        finally:
            # 停止后台智能体
            processing_agent.stop()
            style_agent.stop()
            
            # 取消后台任务
            processing_task.cancel()
            style_task.cancel()
            
            try:
                await processing_task
            except asyncio.CancelledError:
                pass
            
            try:
                await style_task
            except asyncio.CancelledError:
                pass
            
            # 处理队列中剩余的对话
            print("\n正在处理缓存中剩余的对话...")
            await processing_agent.flush_remaining()
            await style_agent.flush_remaining()
            print("✓ 缓存处理完成")
            
            # 询问是否保存
            await self.save_persona_prompt()
    
    async def impersonation_mode(self):
        """扮演模式"""
        print("\n" + "="*50)
        print(f"扮演模式 - 模拟 {self.current_persona}")
        print("="*50)
        print("提示: 输入 'quit' 退出扮演模式\n")
        
        # 创建扮演智能体
        impersonation_agent = ImpersonationAgent(
            knowledge_base=self.persona_data["knowledge_base"],
            style_base=self.persona_data["style_base"],
            oral_habits_base=self.persona_data["oral_habits_base"],
            history=self.persona_data["history"],
            persona_name=self.current_persona,
            max_recent_dialogue=MAX_RECENT_DIALOGUE
        )
        
        print(f"现在你可以与模拟的'{self.current_persona}'对话了！\n")
        
        # 对话循环
        while True:
            user_input = input("你: ").strip()
            
            if user_input.lower() == 'quit':
                print("\n正在退出扮演模式...")
                break
            
            if not user_input:
                continue
            
            print(f"\n{self.current_persona}: ", end="")
            await impersonation_agent.generate_response(user_input)
    
    async def save_persona_prompt(self):
        """提示保存人物数据"""
        save = input("\n是否保存对人物的更改？(yes/no): ").strip().lower()
        
        if save == "yes":
            success = self.persona_manager.save_persona(
                persona_name=self.current_persona,
                knowledge_base=self.persona_data["knowledge_base"],
                style_base=self.persona_data["style_base"],
                oral_habits_base=self.persona_data["oral_habits_base"],
                history=self.persona_data["history"]
            )
            
            if success:
                print(f"✓ 已保存人物数据: {self.current_persona}")
            else:
                print("保存失败")
        else:
            print("未保存，本次更改已丢弃")
    
    async def run(self):
        """主运行循环"""
        while True:
            self.show_menu()
            choice = input("请选择 (1-4): ").strip()
            
            if choice == "1":
                if self.load_persona():
                    await self.mode_loop()
            
            elif choice == "2":
                if self.create_new_persona():
                    await self.mode_loop()
            
            elif choice == "3":
                self.manage_personas()
            
            elif choice == "4":
                print("\n感谢使用 RE-DEMO！再见！")
                break
            
            else:
                print("无效选择，请重试")
    
    async def mode_loop(self):
        """模式选择循环"""
        while True:
            self.show_mode_menu()
            choice = input("请选择 (1-2 或 0): ").strip()
            
            if choice == "1":
                await self.interview_mode()
            
            elif choice == "2":
                await self.impersonation_mode()
            
            elif choice == "0":
                break
            
            else:
                print("无效选择，请重试")


async def main():
    """主入口"""
    app = REDemo()
    try:
        await app.run()
    except KeyboardInterrupt:
        print("\n\n程序被中断")
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
