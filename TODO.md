# TODO List

## High Priority

### Vector Store and Search Improvements
- [ ] Replace filename-based IDs with UUID in `vector_store.py`
  - Update ID generation in `upsert_embedding` method
  - Ensure consistency across GCS, Firestore, and Vector Search index
  - Add migration script for existing data
- [ ] Enhance similarity calculation in `vector_search.py`
  - Improve cosine similarity calculation accuracy
  - Add configurable similarity thresholds
  - Implement better normalization for search scores
  - Add support for different distance metrics

### Performance Optimizations
- [ ] Implement batch processing for vector uploads
- [ ] Add caching layer for frequently accessed metadata
- [ ] Optimize Firestore queries with composite indexes
- [ ] Add connection pooling for database clients

### Error Handling and Reliability
- [ ] Add retry mechanism for failed API calls
- [ ] Implement circuit breaker pattern for external services
- [ ] Add data validation for embeddings and metadata
- [ ] Improve error reporting and monitoring

## Medium Priority

### Code Quality
- [ ] Add comprehensive unit tests for vector operations
- [ ] Implement input validation across all services
- [ ] Add type hints to all functions
- [ ] Create API documentation using OpenAPI/Swagger

### Features
- [ ] Add support for bulk operations (upload/delete)
- [ ] Implement versioning for embeddings
- [ ] Add support for custom metadata schemas
- [ ] Implement search filters based on metadata

### Infrastructure
- [ ] Set up monitoring for vector search performance
- [ ] Add metrics collection for similarity scores
- [ ] Implement auto-scaling policies
- [ ] Add backup and restore procedures

## Low Priority

### Developer Experience
- [ ] Add development environment setup script
- [ ] Improve logging format and levels
- [ ] Create example notebooks for common operations
- [ ] Add contribution guidelines

### Documentation
- [ ] Add architecture decision records (ADRs)
- [ ] Create troubleshooting guide
- [ ] Document performance optimization tips
- [ ] Add benchmarking documentation 