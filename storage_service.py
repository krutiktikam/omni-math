import aiofiles
import json
import os
import asyncio
import pandas as pd
from pathlib import Path
from typing import List, Optional, Union
from config import settings
from schemas import MatrixDataset, MatrixRow
import logging
from datetime import datetime

logger = logging.getLogger("omnimath.storage")

class StorageService:
    def __init__(self, base_path: Path = settings.storage_path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _dataset_to_df(self, dataset: MatrixDataset) -> pd.DataFrame:
        """Helper to convert MatrixDataset to a pandas DataFrame."""
        data = [row.values for row in dataset.rows]
        df = pd.DataFrame(data)
        # Store metadata in the dataframe's attrs if needed, 
        # but Parquet is better for the raw matrix data.
        df.attrs['name'] = dataset.name
        df.attrs['created_at'] = dataset.created_at.isoformat()
        if dataset.metadata:
            df.attrs.update(dataset.metadata)
        return df

    async def save_dataset_json(self, dataset: MatrixDataset) -> str:
        filename = f"{dataset.name.replace(' ', '_')}_{int(dataset.created_at.timestamp())}.json"
        file_path = self.base_path / filename
        try:
            async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
                await f.write(dataset.model_dump_json(indent=2))
            return filename
        except Exception as e:
            logger.error(f"JSON save failed: {e}")
            raise

    async def save_dataset_parquet(self, dataset: MatrixDataset) -> str:
        """Saves dataset as a compressed Parquet file (Optimized for HDD)."""
        filename = f"{dataset.name.replace(' ', '_')}_{int(dataset.created_at.timestamp())}.parquet"
        file_path = self.base_path / filename
        
        try:
            df = self._dataset_to_df(dataset)
            # Use to_thread to prevent blocking the event loop during heavy I/O and compression
            await asyncio.to_thread(df.to_parquet, file_path, engine='pyarrow', compression='snappy')
            logger.info(f"Successfully saved Parquet: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Parquet save failed: {e}")
            raise

    async def list_datasets(self) -> List[str]:
        return [f.name for f in self.base_path.glob("*") if f.suffix in ('.json', '.parquet')]

    async def get_dataset(self, filename: str) -> Optional[Union[MatrixDataset, dict]]:
        file_path = self.base_path / filename
        if not file_path.exists():
            return None

        try:
            if file_path.suffix == '.json':
                async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                    content = await f.read()
                    return MatrixDataset.model_validate(json.loads(content))
            
            elif file_path.suffix == '.parquet':
                # Read parquet into DF, then back to MatrixDataset
                df = await asyncio.to_thread(pd.read_parquet, file_path)
                rows = [MatrixRow(values=row.tolist()) for _, row in df.iterrows()]
                return MatrixDataset(
                    name=filename.split('_')[0], # Simplified recovery
                    rows=rows,
                    created_at=datetime.fromtimestamp(int(filename.split('_')[-1].split('.')[0]))
                )
        except Exception as e:
            logger.error(f"Read failed for {filename}: {e}")
            raise

storage_service = StorageService()
