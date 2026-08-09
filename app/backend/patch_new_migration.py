file_path = r"D:\projects\chatbot-hospital-system\app\backend\alembic\versions\704142b14459_fix_cdi_v2_final_model_alignments.py"  # noqa: E501

with open(file_path) as f:
    content = f.read()

# Replace graph_mentions
content = content.replace(
    "    with op.batch_alter_table('graph_mentions', schema=None) as batch_op:\n        batch_op.drop_constraint(None, type_='foreignkey')",  # noqa: E501
    """    with op.batch_alter_table('graph_mentions', schema=None) as batch_op:
        if batch_op.impl.dialect.name != 'sqlite':
            batch_op.drop_constraint('graph_mentions_entity_id_fkey', type_='foreignkey')""",
)

# Replace graph_relation_assertions
content = content.replace(
    "    with op.batch_alter_table('graph_relation_assertions', schema=None) as batch_op:\n        batch_op.create_unique_constraint('uq_graph_assertion_patient_id', ['patient_id', 'id'])\n        batch_op.drop_constraint(None, type_='foreignkey')\n        batch_op.drop_constraint(None, type_='foreignkey')",  # noqa: E501
    """    with op.batch_alter_table('graph_relation_assertions', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_graph_assertion_patient_id', ['patient_id', 'id'])
        if batch_op.impl.dialect.name != 'sqlite':
            batch_op.drop_constraint('graph_relation_assertions_object_entity_id_fkey', type_='foreignkey')
            batch_op.drop_constraint('graph_relation_assertions_subject_entity_id_fkey', type_='foreignkey')""",
)

# Replace graph_relation_evidence
content = content.replace(
    "    with op.batch_alter_table('graph_relation_evidence', schema=None) as batch_op:\n        batch_op.drop_constraint(None, type_='foreignkey')",  # noqa: E501
    """    with op.batch_alter_table('graph_relation_evidence', schema=None) as batch_op:
        if batch_op.impl.dialect.name != 'sqlite':
            batch_op.drop_constraint('graph_relation_evidence_assertion_id_fkey', type_='foreignkey')""",
)

# Replace legacy_graph_entities create foreign key
content = content.replace(
    "batch_op.create_foreign_key(None, 'patients', ['patient_id'], ['id'])",
    "batch_op.create_foreign_key('fk_legacy_graph_entities_patient', 'patients', ['patient_id'], ['id'])",
)

with open(file_path, "w") as f:
    f.write(content)

print("Migration patched successfully.")
