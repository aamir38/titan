import unittest
from unittest.mock import patch
import asyncio
import json
import os
import GPUtil
import aioredis

# Assuming your module is named gpu_resource_monitor.py
import gpu_resource_monitor

class TestGpuResourceMonitor(unittest.TestCase):

    @patch('GPUtil.getGPUs')
    async def test_get_gpu_load_success(self, mock_getGPUs):
        # Mock GPUtil.getGPUs to return a list with a mock GPU
        mock_gpu = Mock()
        mock_gpu.load = 0.5
        mock_gpu.memoryUsed = 1000
        mock_gpu.memoryTotal = 2000
        mock_gpu.temperature = 50
        mock_getGPUs.return_value = [mock_gpu]

        # Call the function
        load, memory, temp = await gpu_resource_monitor.get_gpu_load()

        # Assert that the function returns the expected values
        self.assertEqual(load, 0.5)
        self.assertEqual(memory, 0.5)
        self.assertEqual(temp, 50)

    @patch('GPUtil.getGPUs')
    async def test_get_gpu_load_no_gpu(self, mock_getGPUs):
        # Mock GPUtil.getGPUs to return an empty list (no GPUs found)
        mock_getGPUs.return_value = []

        # Call the function
        load, memory, temp = await gpu_resource_monitor.get_gpu_load()

        # Assert that the function returns the expected values
        self.assertEqual(load, 0.0)
        self.assertEqual(memory, 0.0)
        self.assertEqual(temp, 0.0)

    @patch('GPUtil.getGPUs')
    async def test_get_gpu_load_exception(self, mock_getGPUs):
        # Mock GPUtil.getGPUs to raise an exception
        mock_getGPUs.side_effect = Exception("GPU access error")

        # Call the function
        load, memory, temp = await gpu_resource_monitor.get_gpu_load()

        # Assert that the function returns the expected values
        self.assertIsNone(load)
        self.assertIsNone(memory)
        self.assertIsNone(temp)

if __name__ == '__main__':
    unittest.main()