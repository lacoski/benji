import unittest

from . import StorageTestCase


class StorageTestB2(StorageTestCase, unittest.TestCase):
    CONFIG = """
        configurationVersion: '1.0.0'
        logFile: /dev/stderr
        databaseEngine: sqlite://
        defaultStorage: b2-1
        
        storages:
        - name: b2-1
          module: b2
          storageId: 1
          configuration:
            accountIdFile: ../../../.b2-account-id.txt
            applicationKeyFile: ../../../.b2-application-key.txt
            bucketName: elemental-backy2-test
            accountInfoFile: {testpath}/b2_account_info
            writeObjectAttempts: 3
            readObjectAttempts: 3
            uploadAttempts: 5
            consistencyCheckWrites: True
            simultaneousWrites: 5
            simultaneousReads: 5
            activeTransforms:
              - k1
              - zstd
            
            
        transforms:
        - name: zstd
          module: zstd
          configuration:
            level: 1
        - name: k1
          module: aes_256_gcm
          configuration:
            masterKey: !!binary |
              e/i1X4NsuT9k+FIVe2kd3vtHVkzZsbeYv35XQJeV8nA=
                
        ios:
            - name: file
              module: file  
        """


if __name__ == '__main__':
    unittest.main()
