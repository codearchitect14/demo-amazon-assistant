from rag.rag_pipeline import retrieve_context, generate_answer


def test_retrieve_context():
    ctx = retrieve_context("What are the ingredients?")
    assert isinstance(ctx, list)


def test_generate_answer():
    answer = generate_answer(["context"], "What is this?")
    assert isinstance(answer, str)
