# 原始资料

原始资料在已指定的私有Drive目录保存；本目录默认忽略原始文件。私人Drive链接不公开。

复算DOF：
```bash
python scripts/build_dof_baseline.py --download
```

下载地址在脚本中，为官方DOF公开工作簿。2026年5月版本的预期SHA-256已固定；若源文件更新，先核对修订后再调整版本，不静默替换。也可从Drive下载原文件，使用`--input 本地路径`离线复算。
