DELETE
FROM ir_config_parameter
WHERE key in ('cloud_storage_google_bucket_name',
              'cloud_storage_azure_container_name',
              'cloud_storage_azure_tenant_id',
              'cloud_storage_azure_client_id',
              'cloud_storage_azure_client_secret')