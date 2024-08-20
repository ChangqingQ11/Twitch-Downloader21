from ui import create_ui

def main():
    app = create_ui(reset_config=True)  # 启动时重置配置
    app.mainloop()

if __name__ == '__main__':
    main()
