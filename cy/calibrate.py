#!/usr/bin/env python3
"""
BeepBeep系统校准工具
在已知距离下运行，自动计算系统延迟偏移
"""

import numpy as np
import sys
import os

# 添加common目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common'))

from config import CALIBRATION_DISTANCE, SOUND_SPEED

def main():
    print("=" * 60)
    print("BeepBeep 系统校准工具")
    print("=" * 60)
    print()
    
    # 读取实际距离
    try:
        true_dist = float(input(f"请输入两设备的实际距离（米）[默认{CALIBRATION_DISTANCE}m]: ").strip() or CALIBRATION_DISTANCE)
    except ValueError:
        true_dist = CALIBRATION_DISTANCE
    
    print(f"\n✓ 实际距离设定为: {true_dist:.2f} 米")
    print("\n请按以下步骤操作：")
    print("1. 将两设备固定在距离 {:.2f} 米的位置".format(true_dist))
    print("2. 分别启动锚节点和目标设备程序")
    print("3. 进行至少5次测量")
    print("4. 记录下测量得到的距离值，输入到此程序")
    print()
    
    measurements = []
    print("请输入测量结果（每次一个，输入'q'结束）：")
    
    while True:
        try:
            inp = input(f"第{len(measurements)+1}次测量距离（米）: ").strip()
            if inp.lower() == 'q':
                break
            
            dist = float(inp)
            if dist <= 0:
                print("  ⚠ 距离必须为正数，请重新输入")
                continue
                
            measurements.append(dist)
            print(f"  ✓ 已记录: {dist:.2f} 米")
            
        except ValueError:
            print("  ⚠ 无效输入，请输入数字或'q'退出")
    
    if len(measurements) < 3:
        print("\n❌ 测量次数太少（至少需要3次），校准失败")
        return
    
    # 统计分析
    measurements = np.array(measurements)
    mean_measured = np.mean(measurements)
    std_measured = np.std(measurements)
    
    print("\n" + "=" * 60)
    print("测量统计：")
    print(f"  测量次数: {len(measurements)}")
    print(f"  平均值: {mean_measured:.3f} 米")
    print(f"  标准差: {std_measured:.3f} 米")
    print(f"  实际距离: {true_dist:.3f} 米")
    print(f"  误差: {mean_measured - true_dist:+.3f} 米")
    
    # 计算校准偏移
    distance_error = mean_measured - true_dist
    time_offset = distance_error / SOUND_SPEED
    
    print("\n" + "=" * 60)
    print("校准结果：")
    print(f"  系统延迟偏移: {time_offset:.6f} 秒")
    print(f"  对应距离偏移: {distance_error:.3f} 米")
    
    # 生成配置
    print("\n" + "=" * 60)
    print("请将以下参数更新到 common/config.py 文件中：")
    print("-" * 60)
    print(f"SYSTEM_DELAY_OFFSET = {time_offset:.6f}  # 系统延迟补偿（秒）")
    print("-" * 60)
    
    # 验证校准效果
    print("\n校准后的预期结果：")
    for i, measured in enumerate(measurements, 1):
        calibrated = measured - distance_error
        print(f"  第{i}次: {measured:.2f}m → {calibrated:.2f}m (误差: {calibrated-true_dist:+.2f}m)")
    
    print("\n✓ 校准完成！")
    print("提示：更新config.py后，重新运行测距程序即可使用校准参数")

if __name__ == "__main__":
    main()