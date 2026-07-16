import sys

filepath = 'D:/projects/chatbot-hospital-system/app/backend/src/hospital_ai/api/routes/chat_stream.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_if_not_evidence = False
indent_amount = 4

for i, line in enumerate(lines):
    if line.startswith('    is_chitchat = is_chitchat_query(payload.question)'):
        new_lines.append('    drug_warnings = []\n')
        new_lines.append('    t_embed_ms = 0\n')
        new_lines.append('    t_retrieval_ms = 0\n')
        new_lines.append('    retrieval_svc = None\n\n')
        new_lines.append(line)
    elif line.startswith('        query_embedding = await EmbeddingService(settings).embed(payload.question)'):
        new_lines.append('        t_embed_start = time.perf_counter()\n')
        new_lines.append(line)
        new_lines.append('        t_embed_ms = int((time.perf_counter() - t_embed_start) * 1000)\n')
        new_lines.append('\n')
        new_lines.append('        t_retrieval_start = time.perf_counter()\n')
    elif line.startswith('        if not evidence or not meets_evidence_threshold(evidence[0], retrieval_mode, settings.evidence_threshold):'):
        in_if_not_evidence = True
        
        # INSERT Graph RAG and Drug warnings BEFORE this
        new_lines.append('        # Graph RAG & Drug Check\n')
        new_lines.append('        try:\n')
        new_lines.append('            if effective_patient_id:\n')
        new_lines.append('                query_entities, _ = await extract_entities_and_relations_nlp(payload.question)\n')
        new_lines.append('                if query_entities:\n')
        new_lines.append('                    entity_names = [e.name for e in query_entities]\n')
        new_lines.append('                    graph_ctx = await find_related_entities(\n')
        new_lines.append('                        session, entity_names, max_hops=2, patient_id=effective_patient_id\n')
        new_lines.append('                    )\n')
        new_lines.append('                    if graph_ctx.related_chunk_ids:\n')
        new_lines.append('                        existing_ids = {e.chunk_id for e in evidence}\n')
        new_lines.append('                        graph_only_ids = graph_ctx.related_chunk_ids - existing_ids\n')
        new_lines.append('                        if graph_only_ids:\n')
        new_lines.append('                            graph_evidence = await retrieval_svc.get_chunks_by_ids(\n')
        new_lines.append('                                list(graph_only_ids)[:payload.top_k],\n')
        new_lines.append('                                user_id=current_user.id,\n')
        new_lines.append('                                patient_id=effective_patient_id,\n')
        new_lines.append('                            )\n')
        new_lines.append('                            for ge in graph_evidence:\n')
        new_lines.append('                                ge.metadata["retrieval_method"] = "graph"\n')
        new_lines.append('                            evidence.extend(graph_evidence)\n')
        new_lines.append('        except Exception:\n')
        new_lines.append('            logger.warning("Graph RAG enrichment skipped", exc_info=True)\n\n')
        new_lines.append('        t_retrieval_ms = int((time.perf_counter() - t_retrieval_start) * 1000)\n\n')
        
        new_lines.append('        try:\n')
        new_lines.append('            drug_warnings = await DrugCheckService(session).check_interactions(\n')
        new_lines.append('                query_text=payload.question, patient_id=effective_patient_id\n')
        new_lines.append('            )\n')
        new_lines.append('        except Exception:\n')
        new_lines.append('            logger.warning("Drug interaction check skipped", exc_info=True)\n\n')
        
        # Now un-indent the if block
        new_lines.append('    if not is_chitchat and (not evidence or not meets_evidence_threshold(evidence[0], retrieval_mode, settings.evidence_threshold)):\n')
    elif in_if_not_evidence:
        if line.startswith('        if not is_chitchat:'):
            in_if_not_evidence = False
            new_lines.append(line)
        elif line.startswith('        '):
            new_lines.append(line[4:])
        elif line.startswith('    '):
            # This is an empty line or something that was already unindented
            new_lines.append(line)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Done")
