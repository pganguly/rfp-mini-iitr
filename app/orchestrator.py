from .graph import evaluate_batch_langgraph

def evaluate_batch(suppliers, db_path, mode="mock", model=None, api_key=None, base_url=None, pdf_backend="auto"):
    return evaluate_batch_langgraph(
        suppliers=suppliers,
        db_path=db_path,
        mode=mode,
        model=model,
        api_key=api_key,
        base_url=base_url,
        pdf_backend=pdf_backend,
    )
