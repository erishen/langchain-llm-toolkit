#!/usr/bin/env python3
"""RAG 效果评估脚本

评估指标:
1. 检索质量 - 召回率、精确率、MRR
2. 生成质量 - 相关性、准确性、完整性
3. 响应时间
"""

import time

from langchain_llm_toolkit.rag import RAGSystem


def evaluate_retrieval(rag: RAGSystem, test_cases: list):
    """评估检索质量"""
    print("\n" + "=" * 60)
    print("检索质量评估")
    print("=" * 60)

    total_recall = 0
    total_precision = 0
    total_mrr = 0
    total_time = 0

    for i, case in enumerate(test_cases, 1):
        query = case["query"]
        expected_keywords = case.get("expected_keywords", [])

        start_time = time.time()
        docs = rag.retrieve_documents(query, k=5)
        elapsed = time.time() - start_time

        # 计算关键词命中率（简化版召回率）
        hit_count = 0
        for doc in docs:
            content = doc.page_content.lower()
            for keyword in expected_keywords:
                if keyword.lower() in content:
                    hit_count += 1
                    break

        recall = hit_count / len(expected_keywords) if expected_keywords else 0
        precision = hit_count / len(docs) if docs else 0

        # MRR 计算（简化版）
        mrr = 0
        for rank, doc in enumerate(docs, 1):
            content = doc.page_content.lower()
            if any(kw.lower() in content for kw in expected_keywords):
                mrr = 1 / rank
                break

        total_recall += recall
        total_precision += precision
        total_mrr += mrr
        total_time += elapsed

        print(f"\n[{i}] 问题: {query}")
        print(f"    召回率: {recall:.2%} | 精确率: {precision:.2%} | MRR: {mrr:.2f}")
        print(f"    检索文档数: {len(docs)} | 耗时: {elapsed:.2f}s")

    n = len(test_cases)
    print("\n平均指标:")
    print(f"  召回率: {total_recall/n:.2%}")
    print(f"  精确率: {total_precision/n:.2%}")
    print(f"  MRR: {total_mrr/n:.2f}")
    print(f"  平均耗时: {total_time/n:.2f}s")

    return {
        "recall": total_recall / n,
        "precision": total_precision / n,
        "mrr": total_mrr / n,
        "avg_time": total_time / n,
    }


def evaluate_generation(rag: RAGSystem, test_cases: list, use_rerank: bool = False):
    """评估生成质量"""
    print("\n" + "=" * 60)
    print(f"生成质量评估 {'(使用重排序)' if use_rerank else ''}")
    print("=" * 60)

    total_relevance = 0
    total_accuracy = 0
    total_completeness = 0
    total_time = 0

    for i, case in enumerate(test_cases, 1):
        query = case["query"]
        expected_keywords = case.get("expected_keywords", [])

        start_time = time.time()
        answer, docs = rag.generate_answer(query, k=5, use_rerank=use_rerank)
        elapsed = time.time() - start_time

        answer_lower = answer.lower()

        relevance = 1.0
        accuracy = (
            sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
            / len(expected_keywords)
            if expected_keywords
            else 0
        )
        completeness = min(1.0, len(answer) / 100)

        total_relevance += relevance
        total_accuracy += accuracy
        total_completeness += completeness
        total_time += elapsed

        print(f"\n[{i}] 问题: {query}")
        print(f"    回答: {answer[:200]}..." if len(answer) > 200 else f"    回答: {answer}")
        print(f"    相关性: {relevance:.2%} | 准确性: {accuracy:.2%} | 完整性: {completeness:.2%}")
        print(f"    耗时: {elapsed:.2f}s | 文档数: {len(docs)}")

    n = len(test_cases)
    print("\n平均指标:")
    print(f"  相关性: {total_relevance/n:.2%}")
    print(f"  准确性: {total_accuracy/n:.2%}")
    print(f"  完整性: {total_completeness/n:.2%}")
    print(f"  平均耗时: {total_time/n:.2f}s")

    return {
        "relevance": total_relevance / n,
        "accuracy": total_accuracy / n,
        "completeness": total_completeness / n,
        "avg_time": total_time / n,
    }


def main():
    print("RAG 效果评估工具")
    print("=" * 60)

    print("\n初始化 RAG 系统...")
    rag = RAGSystem(
        vector_store_type="qdrant",
        embedding_type="ollama",
        embedding_model="mxbai-embed-large",
        llm_model="ollama/gemma4",
    )
    rag.llm_integration.timeout = 120
    rag.load_vector_store()

    # 测试用例
    test_cases = [
        {
            "query": "我的面试经历有哪些？",
            "expected_keywords": ["面试", "技术", "项目", "经验"],
        },
        {
            "query": "PayPal 项目的主要工作内容是什么？",
            "expected_keywords": ["PayPal", "AI Calls", "前端", "开发"],
        },
        {
            "query": "我的健康状况如何？",
            "expected_keywords": ["健康", "体重", "维生素", "饮食"],
        },
    ]

    # 评估检索质量
    retrieval_metrics = evaluate_retrieval(rag, test_cases)

    # 评估生成质量（普通模式）
    generation_metrics = evaluate_generation(rag, test_cases, use_rerank=False)

    # 总结
    print("\n" + "=" * 60)
    print("评估总结")
    print("=" * 60)
    print("\n检索质量:")
    print(f"  召回率: {retrieval_metrics['recall']:.2%}")
    print(f"  精确率: {retrieval_metrics['precision']:.2%}")
    print(f"  MRR: {retrieval_metrics['mrr']:.2f}")
    print("\n生成质量:")
    print(f"  相关性: {generation_metrics['relevance']:.2%}")
    print(f"  准确性: {generation_metrics['accuracy']:.2%}")
    print(f"  完整性: {generation_metrics['completeness']:.2%}")

    # 综合评分
    overall_score = (
        retrieval_metrics["recall"] * 0.3
        + retrieval_metrics["precision"] * 0.2
        + generation_metrics["accuracy"] * 0.3
        + generation_metrics["completeness"] * 0.2
    )
    print(f"\n综合评分: {overall_score:.2%}")

    if overall_score >= 0.7:
        print("评级: 优秀 ⭐⭐⭐⭐⭐")
    elif overall_score >= 0.5:
        print("评级: 良好 ⭐⭐⭐⭐")
    elif overall_score >= 0.3:
        print("评级: 一般 ⭐⭐⭐")
    else:
        print("评级: 需改进 ⭐⭐")


if __name__ == "__main__":
    main()
