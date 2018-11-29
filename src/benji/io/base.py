#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from threading import BoundedSemaphore
from typing import Tuple, Union, Optional, List, Generator

from benji.config import _ConfigDict, Config
from benji.logging import logger
from benji.metadata import Block, DereferencedBlock
from benji.utils import future_results_as_completed, parametrized_hash_function


class IOBase(metaclass=ABCMeta):

    READ_QUEUE_LENGTH = 5

    def __init__(self, *, config: Config, name: str, module_configuration: _ConfigDict, path: str,
                 block_size: int) -> None:
        self._name = name
        self._path = path
        self._block_size = block_size
        self._simultaneous_reads = config.get_from_dict(module_configuration, 'simultaneousReads', types=int)
        self._read_executor: Optional[ThreadPoolExecutor] = None

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def size(self) -> int:
        raise NotImplementedError()

    def open_r(self) -> None:
        self._read_executor = ThreadPoolExecutor(max_workers=self._simultaneous_reads, thread_name_prefix='IO-Reader')
        self._read_futures: List[Future] = []
        self._read_semaphore = BoundedSemaphore(self._simultaneous_reads + self.READ_QUEUE_LENGTH)

    @abstractmethod
    def _read(self, block: DereferencedBlock) -> Tuple[DereferencedBlock, bytes]:
        raise NotImplementedError()

    def read(self, block: DereferencedBlock, sync: bool = False):
        if sync:
            return self._read(block)[1]
        else:

            def read_with_acquire():
                self._read_semaphore.acquire()
                return self._read(block)

            self._read_futures.append(self._read_executor.submit(read_with_acquire))  # type: ignore

    def read_get_completed(self, timeout: Optional[int] = None
                          ) -> Generator[Union[Tuple[DereferencedBlock, bytes], BaseException], None, None]:
        return future_results_as_completed(self._read_futures, semaphore=self._read_semaphore, timeout=timeout)

    @abstractmethod
    def open_w(self, size: int, force: bool = False) -> None:
        raise NotImplementedError()

    @abstractmethod
    def write(self, block: DereferencedBlock, data: bytes):
        raise NotImplementedError()

    def close(self) -> None:
        if self._read_executor:
            if len(self._read_futures) > 0:
                logger.warning('IO backend closed with {} outstanding read jobs, cancelling them.'.format(
                    len(self._read_futures)))
                for future in self._read_futures:
                    future.cancel()
                logger.debug('IO backend cancelled all outstanding read jobs.')
                # Get all jobs so that the semaphore gets released and still waiting jobs can complete
                for result in self.read_get_completed():
                    pass
                logger.debug('IO backend read results from all outstanding read jobs.')
            self._read_executor.shutdown()