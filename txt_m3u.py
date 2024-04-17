def txt_to_m3u():   

   # 打开文件并获取文件对象
    file = open("IPTV_Z.m3u", "w")
    
    # 写入单行文本
    file.write("Hello, world!\n")
    
    # 写入多行文本
    lines = ["This is line 1\n", "This is line 2\n", "This is line 3\n"]
    file.writelines(lines)
    
    # 关闭文件
    file.close()

# 将txt文件转换为m3u文件
txt_to_m3u()

print(f"m3u文件创建成功,IPTV_Z.m3u")
