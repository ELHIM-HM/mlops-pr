import argparse
import json
from http import HTTPStatus
from typing import Dict

import pandas as pd
import uvicorn
from fastapi import FastAPI
from starlette.requests import Request

from madewithml import evaluate, predict
from madewithml.config import MLFLOW_TRACKING_URI, mlflow

# Define application
app = FastAPI(
    title="Made With ML",
    description="Classify machine learning projects.",
    version="0.1",
)


async def get_prediction_input(request: Request, title: str = "", description: str = "") -> Dict:
    """Get prediction inputs from a JSON body or query parameters."""
    data = {}
    body = await request.body()
    if body:
        data = json.loads(body)
    return {
        "title": data.get("title", title) or "",
        "description": data.get("description", description) or "",
    }


def create_app(run_id: str, threshold: float = 0.9) -> FastAPI:
    """Create a local FastAPI app for serving without Ray Serve."""
    local_app = FastAPI(
        title="Made With ML",
        description="Classify machine learning projects.",
        version="0.1",
    )
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    best_checkpoint = predict.get_best_checkpoint(run_id=run_id)
    predictor = predict.TorchPredictor.from_checkpoint(best_checkpoint)

    @local_app.get("/")
    def _index() -> Dict:
        response = {
            "message": HTTPStatus.OK.phrase,
            "status-code": HTTPStatus.OK,
            "data": {},
        }
        return response

    @local_app.get("/run_id/")
    def _run_id() -> Dict:
        return {"run_id": run_id}

    @local_app.post("/evaluate/")
    async def _evaluate(request: Request) -> Dict:
        data = await request.json()
        results = evaluate.evaluate(run_id=run_id, dataset_loc=data.get("dataset"))
        return {"results": results}

    @local_app.post("/predict/")
    async def _predict(request: Request, title: str = "", description: str = ""):
        data = await get_prediction_input(request=request, title=title, description=description)
        sample_df = pd.DataFrame([{"title": data["title"], "description": data["description"], "tag": ""}])
        results = predict.predict_proba(df=sample_df, predictor=predictor)

        for i, result in enumerate(results):
            pred = result["prediction"]
            prob = result["probabilities"]
            if prob[pred] < threshold:
                results[i]["prediction"] = "other"

        return {"results": make_json_safe(results)}

    return local_app


def make_json_safe(results):
    """Convert numpy values in prediction results to JSON-safe Python types."""
    safe_results = []
    for result in results:
        safe_results.append(
            {
                "prediction": result["prediction"],
                "probabilities": {label: float(prob) for label, prob in result["probabilities"].items()},
            }
        )
    return safe_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_id", help="run ID to use for serving.")
    parser.add_argument("--threshold", type=float, default=0.9, help="threshold for `other` class.")
    parser.add_argument("--host", default="127.0.0.1", help="host to bind.")
    parser.add_argument("--port", type=int, default=8000, help="port to bind.")
    args = parser.parse_args()
    uvicorn.run(create_app(run_id=args.run_id, threshold=args.threshold), host=args.host, port=args.port)
