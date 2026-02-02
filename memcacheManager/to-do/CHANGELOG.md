# Changelog

All notable changes to the Memcache Manager plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-02

### Added
- Initial release of Memcache Manager plugin
- **Service Detection**
  - Auto-detect Memcached or LSMCD installation
  - Support for both service types with unified interface
  - Marker file detection (`/home/cyberpanel/memcached`, `/home/cyberpanel/lsmcd`)
  - Binary detection (`/usr/bin/memcached`, `/usr/local/lsmcd/bin/lsmcd`)

- **Service Control**
  - Start, Stop, Restart service actions
  - Enable/Disable service at boot
  - Real-time status monitoring
  - Connection testing

- **Statistics Display**
  - Memory usage with doughnut chart visualization
  - Cache hit/miss rate with chart
  - Operations bar chart (GET, SET, DELETE)
  - Quick stats cards for key metrics
  - Auto-refresh every 30 seconds
  - Manual refresh button

- **Cache Operations**
  - Flush all cache data
  - Confirmation dialog before flush
  - Success/error feedback

- **Configuration Display**
  - Service type and name
  - Host and port settings
  - Config file location
  - Parsed configuration settings

- **Raw Stats Output**
  - Complete raw stats from memcache server
  - Scrollable output area

- **API Endpoints**
  - `GET /plugins/memcacheManager/` - Main dashboard
  - `POST /plugins/memcacheManager/api/control/` - Service control
  - `GET /plugins/memcacheManager/api/stats/` - Statistics JSON
  - `POST /plugins/memcacheManager/api/flush/` - Flush cache
  - `GET /plugins/memcacheManager/api/config/` - Configuration JSON

- **UI/UX**
  - Bootstrap cards for organized layout
  - Chart.js integration for visualizations
  - Responsive design for mobile
  - Loading states for buttons
  - Alert messages for feedback
  - Dark theme code display
  - Service type badge

- **Security**
  - CyberPanel login required
  - CSRF protection on POST endpoints
  - Input validation
  - Safe error handling without data leakage

- **Compatibility**
  - AlmaLinux 8.8, 9.6, 10
  - CyberPanel 2.0+
  - OpenLiteSpeed and LiteSpeed Enterprise
  - Memcached 1.5+
  - LSMCD all versions

### Technical Details
- Python/Django plugin architecture
- Socket-based communication with memcache (no external CLI dependencies)
- Systemctl integration for service management
- Comprehensive error handling and logging

## Future Plans

### [1.1.0] - Planned
- [ ] Slab statistics display
- [ ] Per-item statistics
- [ ] Connection history graph
- [ ] Memory usage trend chart
- [ ] Multi-server support
- [ ] Custom port configuration
- [ ] Config file editor (read-only initially)

### [1.2.0] - Planned
- [ ] Item browser (view cached keys)
- [ ] Manual item deletion
- [ ] TTL management
- [ ] Export statistics to CSV/JSON
- [ ] Email alerts for high memory usage
- [ ] Webhook integration

---

## Contributing

Contributions are welcome! Please submit pull requests or open issues for:
- Bug reports
- Feature requests
- Documentation improvements
- Code optimizations
