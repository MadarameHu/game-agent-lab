# platformer-04 — 把明亮玩具群岛改为清晰可读的黄昏关卡

原布局与玩法不变，加入橙紫黄昏天空、暖云、下坠平台警示斜纹和协调金币HUD。

改动限定视觉：橙色地平线过渡到淡紫天空，暖色太阳搭配偏冷环境补光；云材质采用暖桃色。下坠平台复用原模型与colormap，并用橙红斜纹区分危险表面。金币HUD保留原字体与贴图，加入深紫面板、暖金字色、阴影和28像素留白。没有全屏颜色滤镜。

44个原世界/角色/相机节点区块完全一致，61个玩法/碰撞/模型/字体文件字节不变；14枚金币和3个下坠平台运行时核对通过。测试将一个原金币移动到玩家以触发真实碰撞并确认HUD显示1，再将玩家放到原下坠平台上触发实际下落。上述位置注入只在截图后发生，产品与截图的关卡布局保持原样。

图像证据：`evidence/final/scene.png` 为原出生相机；`overview.png` 为全局审查图，`remote.png` 为远端平台审查图。后两张相机为测试注入，产品相机没有修改。第一版补光不足的图像保留在 `evidence/native-attempt1`。

## 启动

```sh
"/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/work/pipeline-build/runtime/Godot.app/Contents/MacOS/Godot" --path "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-04/project" --rendering-method gl_compatibility
```

直接启动该项目即可游玩。Godot 4.7.2，1280×720，Compatibility renderer。原MIT/CC0/OFL许可文件保留。

## 已执行验证与复查

```sh
"/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/work/pipeline-build/runtime/Godot.app/Contents/MacOS/Godot" --headless --editor --import --path "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-04/project" --quit
"/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/work/pipeline-build/runtime/Godot.app/Contents/MacOS/Godot" --path "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-04/project" --rendering-method gl_compatibility --resolution 1280x720 --script "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-04/verification/render.gd" -- "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-04/evidence/final"
python3 "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-04/verification/preservation.py"
python3 "/Users/hjw/Documents/Codex/2026-09-19/agentic-game-development-as-a-verifiable/outputs/game-cases-v1/cases/platformer-04/verification/check_result.py"
```

最终结果为 `evidence/final/result.json`，候选与验证器哈希已冻结；`check_result.py`会因文件变化或检查失败而失败。导入后的原始资源重写由执行脚本恢复，详见 `evidence/import/restored-import-rewrites.json`；直接重跑导入可能产生Godot资源格式重写，此时哈希检查会正确报告变化。native渲染批量运行必须先取得 `work/game-batch-11/native-render.lock` 独占锁（本次已取得）。

## 验收边界

- 黄昏氛围、远近层次、角色/旗帜/落点识别度仍待人工验收；自动渲染成功不能替代视觉评分。
- scene.png为原出生相机；overview.png与remote.png为明确注入的审查相机，产品相机没有修改。
- 金币与下坠测试在完成截图后注入位置以触发原物理碰撞；未声称从出生点完整人工通关。
- 仅校准并验证Compatibility；Forward+具有设置但未经本轮渲染验收。
- 平台项目没有用户存档读写；测试未生成或修改user://持久存档。
- Godot退出时已知资源清理告警，无运行SCRIPT ERROR。

状态：`awaiting_human`；`engine_reward=1`，`human_review=null`，`combined_reward=null`。未把实现者视觉观察计为人工通过。
