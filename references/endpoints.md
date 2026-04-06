# CSQAQ Endpoints

| Method | Path | Operation ID | Doc | Summary |
|---|---|---|---|---|
| `GET` | `/api/v1/current_data` | `______________api_v1_current_data_get` | `api-187131779` | 获取首页相关数据 |
| `POST` | `/api/v1/goods/getPriceByMarketHashName` | `__good_____api_v1_info_good_get` | `api-283470032` | 批量获取饰品出售价格数据 |
| `POST` | `/api/v1/goods/get_all_goods_id` | `__good_____api_v1_info_good_get` | `api-337690892` | 获取全量站内饰品ID |
| `POST` | `/api/v1/goods/get_all_goods_info` | `__good_____api_v1_info_good_get` | `api-327138094` | 获取全量饰品价格数据 |
| `POST` | `/api/v1/goods/get_all_goods_rank` | `__good_____api_v1_info_good_get` | `api-337683199` | 获取全量饰品排行榜数据 |
| `POST` | `/api/v1/goods/get_goods_template` | `__good_____api_v1_info_good_get` | `api-366480732` | 获取饰品模板数据 |
| `POST` | `/api/v1/info/chart` | `__good_____api_v1_info_chart_post` | `api-187131781` | 获取单件饰品图表数据 |
| `POST` | `/api/v1/info/chartAll` | `____good_____api_v1_info_chartAll_post` | `api-187131782` | 获取单件饰品全量图表数据 (暂停使用) |
| `POST` | `/api/v1/info/container_data_info` | `________api_v1_info_container_data_info_post` | `api-187131826` | 获取所有收藏品列表 |
| `POST` | `/api/v1/info/exchange_detail` | `___________api_v1_info_exchange_detail_post` | `api-187131823` | 获取挂刀行情详情信息 |
| `POST` | `/api/v1/info/get_banana_chart` | `____Banana_chart___api_v1_info_get_banana_chart_post` | `api-187131828` | 获取单件Banana图表数据 |
| `POST` | `/api/v1/info/get_banana_data` | `____Banana_good___api_v1_info_get_banana_data_post` | `api-187131827` | 获取所有Banana列表数据 |
| `POST` | `/api/v1/info/get_good_id` | `__good_id___api_v1_info_get_good_id_post` | `api-187131777` | 获取饰品的ID信息 |
| `POST` | `/api/v1/info/get_page_list` | `________api_v1_info_get_page_list_post` | `api-187131775` | 获取饰品列表信息 |
| `POST` | `/api/v1/info/get_popular_goods` | `_______api_v1_info_get_series_list_post` | `api-327157635` | 获取全量饰品热度排名 |
| `POST` | `/api/v1/info/get_rank_list` | `__rank_____api_v1_info_get_rank_list_post` | `api-187131776` | 获取排行榜单信息接口 |
| `GET` | `/api/v1/info/get_series_detail` | `_______api_v1_info_get_series_detail_get` | `api-187131804` | 获取单件热门系列饰品详情 |
| `POST` | `/api/v1/info/get_series_list` | `_______api_v1_info_get_series_list_post` | `api-187131803` | 获取热门系列饰品列表 |
| `GET` | `/api/v1/info/good` | `__good_____api_v1_info_good_get` | `api-187131780` | 获取单件饰品详情 |
| `GET` | `/api/v1/info/good/container_detail` | `___________api_v1_info_good_container_detail_get` | `api-187131825` | 获取单个收藏品的包含物 |
| `GET` | `/api/v1/info/good/statistic` | `__good_____api_v1_info_good_get` | `api-366480669` | 获取单件饰品存世量走势 |
| `POST` | `/api/v1/info/roi` | `__________api_v1_stat_case_get` | `api-294405260` | 获取武器箱开箱回报率列表 |
| `GET` | `/api/v1/info/roi_detail` | `__________api_v1_stat_case_get` | `api-327163706` | 获取单个武器箱开箱回报率走势 |
| `POST` | `/api/v1/info/simple/chartAll` | `__good_____api_v1_info_chart_post` | `api-278065737` | 获取单件饰品k线数据 |
| `POST` | `/api/v1/info/vol_data_detail` | `__________api_v1_info_vol_data_detail_post` | `api-187131822` | 获取成交量图表/磨损信息 |
| `POST` | `/api/v1/info/vol_data_info` | `__________api_v1_info_vol_data_info_post` | `api-187131821` | 获取成交量数据信息 |
| `POST` | `/api/v1/monitor/get_task_list` | `__________________api_v1_monitor_get_task_list_post` | `api-187131810` | 获取库存监控任务列表 |
| `POST` | `/api/v1/monitor/get_task_trends` | `____________api_v1_monitor_get_task_trends_post` | `api-187131809` | 获取库存监控最新动态 |
| `POST` | `/api/v1/monitor/rank` | `_____________api_v1_monitor_rank_post` | `api-187131813` | 获取库存监控持有量排行榜 |
| `GET` | `/api/v1/search/suggest` | `` | `api-189290586` | 联想查询饰品的ID信息 |
| `GET` | `/api/v1/stat/case` | `__________api_v1_stat_case_get` | `api-187131788` | 获取武器箱开箱数量统计 |
| `POST` | `/api/v1/stat/case/chart` | `__case_______api_v1_stat_case_chart_post` | `api-187131799` | 获取单个武器箱历史开箱量 |
| `GET` | `/api/v1/sub/kline` | `` | `api-278085071` | 获取指数K线图 |
| `GET` | `/api/v1/sub_data` | `` | `api-230764015` | 获取指数详情数据 |
| `POST` | `/api/v1/sys/bind_local_ip` | `` | `api-342090738` | 绑定本机白名单IP |
| `POST` | `/api/v1/task/get_task_all` | `______________api_v1_task_get_task_all_post` | `api-187131815` | 获取监控单个用户全部库存 |
| `POST` | `/api/v1/task/get_task_business` | `________________api_v1_task_get_task_info_post` | `api-358158458` | 获取监控单个用户库存动态 |
| `POST` | `/api/v1/task/get_task_info` | `________________api_v1_task_get_task_info_post` | `api-187131814` | 获取监控单个用户信息 |
| `POST` | `/api/v1/task/get_task_recent` | `______________api_v1_task_get_task_all_post` | `api-343919624` | 获取监控单个用户库存快照列表 |
