# 数据分析页面 RAG 智能查询问题修复计划

## 问题概述

数据分析页面的 RAG 智能查询功能报错，无法正常使用。

## 问题分析

### 1. 错误现象

当用户在数据分析页面执行 RAG 智能查询时，后端返回错误：

```
chromadb.errors.InvalidArgumentError: Collection expecting embedding with dimension of 384, got 1024
```

### 2. 根本原因

**向量维度不匹配**：

| 组件 | 向量维度 | 说明 |
|------|---------|------|
| ChromaDB 集合 | 384 维 | 使用默认 embedding 函数（all-MiniLM-L6-v2）创建 |
| DashScope Embedding | 1024 维 | text-embedding-v3 模型输出 |

**问题代码位置**：

1. **存储时** - [store_node.py:108-112](file:///d:/Documents/CodeProjects/ResumeScreening/src/workflows/store_node.py#L108-L112)
   ```python
   chroma_client.add_documents(
       ids=[talent_id],
       documents=[resume_text],
       metadatas=[metadata],
   )  # 未提供 embeddings 参数，ChromaDB 使用默认函数生成 384 维向量
   ```

2. **查询时** - [rag_service.py:120-128](file:///d:/Documents/CodeProjects/ResumeScreening/src/utils/rag_service.py#L120-L128)
   ```python
   query_vector = await self._embedding_service.embed_query(query)  # 生成 1024 维向量
   results = self._chroma_client.query(
       query_embeddings=[query_vector],  # 维度不匹配！
       ...
   )
   ```

### 3. 问题链路

```
简历上传 → store_node → ChromaDB 存储（384维，默认函数）
                              ↓
用户查询 → rag_service → DashScope Embedding（1024维）→ ChromaDB 查询
                              ↓
                        维度不匹配错误！
```

## 修复方案

### 方案：统一使用 DashScope Embedding

**核心思路**：在存储和查询时都使用 DashScope Embedding API，确保向量维度一致。

### 修改清单

#### 1. 修改 `store_node.py`

**文件**: [src/workflows/store_node.py](file:///d:/Documents/CodeProjects/ResumeScreening/src/workflows/store_node.py)

**修改内容**：
- 将同步函数 `_store_to_chromadb` 改为异步函数
- 在存储前使用 `EmbeddingService` 生成向量
- 传递 `embeddings` 参数给 ChromaDB

```python
async def _store_to_chromadb(
    talent_id: str,
    resume_text: str,
    candidate_info: dict[str, Any],
) -> bool:
    """存储简历向量到 ChromaDB。"""
    if not resume_text:
        logger.warning("简历文本为空，跳过向量存储")
        return False

    try:
        # 使用 DashScope Embedding 生成向量
        from src.utils.embedding import get_embedding_service
        
        embedding_service = get_embedding_service()
        embeddings = await embedding_service.embed_texts([resume_text])
        
        if not embeddings:
            logger.warning("向量生成失败，跳过存储")
            return False

        # 构建元数据
        is_qualified = candidate_info.get("is_qualified", False)
        metadata = {
            "name": candidate_info.get("name", ""),
            "school": candidate_info.get("school", ""),
            ...
        }

        # 添加到 ChromaDB（带向量）
        chroma_client.add_documents(
            ids=[talent_id],
            documents=[resume_text],
            metadatas=[metadata],
            embeddings=embeddings,  # 关键：使用 DashScope 生成的向量
        )

        logger.info(f"向量存储成功: talent_id={talent_id}")
        return True
    except Exception as e:
        ...
```

#### 2. 修改 `store_node` 函数调用

**文件**: [src/workflows/store_node.py](file:///d:/Documents/CodeProjects/ResumeScreening/src/workflows/store_node.py)

**修改内容**：
- 将同步调用改为异步调用

```python
# 4. 存储向量到 ChromaDB
if state.text_content:
    await _store_to_chromadb(  # 改为 await
        talent_id,
        state.text_content,
        state.candidate_info,
    )
```

#### 3. 清空现有 ChromaDB 数据

由于现有数据的向量维度是 384 维，与新方案不兼容，需要清空后重新生成。

**操作**：
1. 删除 `data/chroma` 目录下的所有数据
2. 或使用脚本清空集合并重新向量化现有人才数据

#### 4. 可选：添加批量向量化脚本

创建脚本用于重新向量化现有人才数据：

**文件**: [scripts/rebuild_chroma_vectors.py](file:///d:/Documents/CodeProjects/ResumeScreening/scripts/rebuild_chroma_vectors.py)

```python
"""重新构建 ChromaDB 向量索引。"""

async def rebuild_vectors():
    """重新向量化所有人才数据。"""
    # 1. 清空现有集合
    # 2. 从 MySQL 读取所有人才数据
    # 3. 使用 DashScope Embedding 生成向量
    # 4. 存储到 ChromaDB
```

## 验证步骤

### 1. 单元测试

```bash
# 测试 Embedding 服务
uv run python scripts/test_rag.py
```

### 2. 集成测试

1. 启动后端服务
2. 上传一份简历
3. 在数据分析页面执行 RAG 查询
4. 验证返回结果正常

### 3. API 测试

```bash
# 测试 RAG 查询 API
curl -X POST http://localhost:8000/api/v1/analysis/query-with-analytics \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query": "有大数据开发经验的候选人", "top_k": 5}'
```

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 现有数据丢失 | 高 | 先备份 MySQL 数据，可重新向量化恢复 |
| Embedding API 调用失败 | 中 | 添加重试机制和降级处理 |
| 性能影响 | 低 | 异步处理，不阻塞主流程 |

## 时间估算

| 任务 | 预计时间 |
|------|---------|
| 修改 store_node.py | 15 分钟 |
| 清空 ChromaDB 数据 | 5 分钟 |
| 测试验证 | 10 分钟 |
| **总计** | **30 分钟** |

## 相关文件

- [src/workflows/store_node.py](file:///d:/Documents/CodeProjects/ResumeScreening/src/workflows/store_node.py) - 入库节点
- [src/utils/rag_service.py](file:///d:/Documents/CodeProjects/ResumeScreening/src/utils/rag_service.py) - RAG 服务
- [src/utils/embedding.py](file:///d:/Documents/CodeProjects/ResumeScreening/src/utils/embedding.py) - Embedding 服务
- [src/storage/chroma_client.py](file:///d:/Documents/CodeProjects/ResumeScreening/src/storage/chroma_client.py) - ChromaDB 客户端
- [src/api/v1/analysis.py](file:///d:/Documents/CodeProjects/ResumeScreening/src/api/v1/analysis.py) - 数据分析 API
