"""
热门城市行程模板 — 秒出方案，不需要等 LLM。
每个模板不含 transport_info 和 weather_info，由路由层根据请求动态注入。
"""
TEMPLATES = {
    "北京": {
        "city": "北京",
        "days": [
            {
                "date": "", "day_index": 0,
                "description": "皇城文化之旅：感受千年古都的厚重历史",
                "transportation": "地铁",
                "accommodation": "前门/王府井区域酒店",
                "attractions": [
                    {"name": "天安门广场", "address": "北京市东城区", "visit_duration": 60, "description": "世界最大的城市中心广场，感受祖国心脏的庄严与宏伟", "ticket_price": 0, "category": "历史", "rating": 4.8, "location": {"longitude": 116.397428, "latitude": 39.90923}},
                    {"name": "故宫博物院", "address": "北京市东城区景山前街4号", "visit_duration": 240, "description": "明清两代皇家宫殿，世界上保存最完整的木质结构古建筑群", "ticket_price": 60, "category": "历史", "rating": 4.9, "location": {"longitude": 116.397026, "latitude": 39.918058}},
                    {"name": "景山公园", "address": "北京市西城区景山西街44号", "visit_duration": 60, "description": "俯瞰故宫全景的最佳位置，万春亭是中轴线最高点", "ticket_price": 2, "category": "公园", "rating": 4.5, "location": {"longitude": 116.396986, "latitude": 39.925195}},
                ],
                "meals": [
                    {"type": "lunch", "name": "故宫冰窖餐厅", "estimated_cost": 80},
                    {"type": "dinner", "name": "四季民福烤鸭店", "estimated_cost": 150},
                ],
            },
            {
                "date": "", "day_index": 1,
                "description": "长城雄风：不到长城非好汉",
                "transportation": "S2市郊铁路",
                "accommodation": "前门/王府井区域酒店",
                "attractions": [
                    {"name": "八达岭长城", "address": "北京市延庆区G6京藏高速58号出口", "visit_duration": 300, "description": "万里长城最具代表性的段落，气势磅礴，视野开阔", "ticket_price": 40, "category": "历史", "rating": 4.8, "location": {"longitude": 116.004227, "latitude": 40.354518}},
                    {"name": "奥林匹克公园", "address": "北京市朝阳区北辰路", "visit_duration": 90, "description": "鸟巢和水立方所在地，感受现代北京的奥运精神", "ticket_price": 0, "category": "现代", "rating": 4.5, "location": {"longitude": 116.391467, "latitude": 39.992806}},
                ],
                "meals": [
                    {"type": "lunch", "name": "长城脚下农家菜", "estimated_cost": 60},
                    {"type": "dinner", "name": "簋街小龙虾", "estimated_cost": 120},
                ],
            },
            {
                "date": "", "day_index": 2,
                "description": "皇家园林与胡同文化",
                "transportation": "地铁+步行",
                "accommodation": "前门/王府井区域酒店",
                "attractions": [
                    {"name": "颐和园", "address": "北京市海淀区新建宫门路19号", "visit_duration": 180, "description": "中国现存最大的皇家园林，昆明湖与万寿山相映成趣", "ticket_price": 30, "category": "园林", "rating": 4.8, "location": {"longitude": 116.275045, "latitude": 39.999463}},
                    {"name": "南锣鼓巷", "address": "北京市东城区南锣鼓巷", "visit_duration": 90, "description": "北京最古老的街区之一，感受老北京市井文化", "ticket_price": 0, "category": "街区", "rating": 4.3, "location": {"longitude": 116.403019, "latitude": 39.937562}},
                ],
                "meals": [
                    {"type": "lunch", "name": "颐和园听鹂馆", "estimated_cost": 100},
                    {"type": "dinner", "name": "姚记炒肝（鼓楼店）", "estimated_cost": 40},
                ],
            },
        ],
        "overall_suggestions": "1. 故宫、长城需提前在官网实名预约\n2. 办理北京一卡通，地铁公交均享优惠\n3. 5月气温适宜，但早晚温差大，建议带薄外套\n4. 八达岭长城建议乘S2市郊铁路，避免高速堵车\n5. 热门餐厅建议提前排队或预约",
    },
    "上海": {
        "city": "上海",
        "days": [
            {
                "date": "", "day_index": 0,
                "description": "外滩与陆家嘴：感受魔都的双面魅力",
                "transportation": "地铁",
                "accommodation": "南京路/人民广场区域酒店",
                "attractions": [
                    {"name": "外滩", "address": "上海市黄浦区中山东一路", "visit_duration": 90, "description": "万国建筑博览群，隔江眺望陆家嘴天际线", "ticket_price": 0, "category": "地标", "rating": 4.7, "location": {"longitude": 121.490517, "latitude": 31.235931}},
                    {"name": "东方明珠", "address": "上海市浦东新区世纪大道1号", "visit_duration": 120, "description": "上海地标建筑，263米观光层俯瞰全城", "ticket_price": 199, "category": "地标", "rating": 4.5, "location": {"longitude": 121.499763, "latitude": 31.239682}},
                    {"name": "南京路步行街", "address": "上海市黄浦区南京东路", "visit_duration": 90, "description": "中国第一商业街，百年繁华依旧", "ticket_price": 0, "category": "购物", "rating": 4.4, "location": {"longitude": 121.474064, "latitude": 31.236277}},
                ],
                "meals": [
                    {"type": "lunch", "name": "南翔小笼包（城隍庙店）", "estimated_cost": 50},
                    {"type": "dinner", "name": "外滩18号法餐厅", "estimated_cost": 300},
                ],
            },
            {
                "date": "", "day_index": 1,
                "description": "文艺范儿：从法租界到田子坊",
                "transportation": "地铁+步行",
                "accommodation": "南京路/人民广场区域酒店",
                "attractions": [
                    {"name": "武康路", "address": "上海市徐汇区武康路", "visit_duration": 60, "description": "上海最文艺的道路，百年洋房与梧桐树影", "ticket_price": 0, "category": "街区", "rating": 4.6, "location": {"longitude": 121.43752, "latitude": 31.208853}},
                    {"name": "田子坊", "address": "上海市黄浦区泰康路210弄", "visit_duration": 120, "description": "石库门里的创意集市，小店与咖啡馆林立", "ticket_price": 0, "category": "文创", "rating": 4.3, "location": {"longitude": 121.474064, "latitude": 31.208063}},
                    {"name": "新天地", "address": "上海市黄浦区太仓路", "visit_duration": 90, "description": "石库门建筑群改造的时尚休闲区", "ticket_price": 0, "category": "休闲", "rating": 4.4, "location": {"longitude": 121.473701, "latitude": 31.219329}},
                ],
                "meals": [
                    {"type": "lunch", "name": "鼎泰丰（新天地店）", "estimated_cost": 120},
                    {"type": "dinner", "name": "外婆家（田子坊店）", "estimated_cost": 80},
                ],
            },
            {
                "date": "", "day_index": 2,
                "description": "迪士尼奇幻日或朱家角水乡游",
                "transportation": "地铁11号线",
                "accommodation": "南京路/人民广场区域酒店",
                "attractions": [
                    {"name": "朱家角古镇", "address": "上海市青浦区朱家角镇", "visit_duration": 180, "description": "上海周边千年水乡古镇，放生桥、北大街充满江南韵味", "ticket_price": 0, "category": "古镇", "rating": 4.4, "location": {"longitude": 121.055961, "latitude": 31.110217}},
                    {"name": "豫园", "address": "上海市黄浦区安仁街218号", "visit_duration": 90, "description": "江南古典园林，始建于明代，城隍庙商圈核心", "ticket_price": 40, "category": "园林", "rating": 4.5, "location": {"longitude": 121.490633, "latitude": 31.227108}},
                ],
                "meals": [
                    {"type": "lunch", "name": "朱家角扎肉/阿婆粽", "estimated_cost": 40},
                    {"type": "dinner", "name": "城隍庙小吃广场", "estimated_cost": 60},
                ],
            },
        ],
        "overall_suggestions": "1. 外滩夜景最佳观赏时间是晚上7-9点\n2. 东方明珠建议网上提前购票，现场排队较长\n3. 地铁覆盖主要景点，推荐使用Metro大都会App\n4. 5月上海温暖湿润，建议携带雨具\n5. 朱家角建议避开周末，工作日人少体验更佳\n6. 城隍庙小吃推荐南翔小笼、蟹壳黄、排骨年糕",
    },
    "成都": {
        "city": "成都",
        "days": [
            {
                "date": "", "day_index": 0,
                "description": "慢生活：品美食、逛巷子、看大熊猫",
                "transportation": "地铁+步行",
                "accommodation": "春熙路/太古里区域酒店",
                "attractions": [
                    {"name": "大熊猫繁育研究基地", "address": "成都市成华区熊猫大道1375号", "visit_duration": 180, "description": "近距离观赏国宝大熊猫，建议早上8点到达", "ticket_price": 55, "category": "自然", "rating": 4.7, "location": {"longitude": 104.146376, "latitude": 30.733095}},
                    {"name": "宽窄巷子", "address": "成都市青羊区长顺街附近", "visit_duration": 120, "description": "清代古街区，体验老成都的慢生活", "ticket_price": 0, "category": "街区", "rating": 4.4, "location": {"longitude": 104.053594, "latitude": 30.670163}},
                    {"name": "锦里", "address": "成都市武侯区武侯祠大街231号", "visit_duration": 90, "description": "西蜀第一街，古色古香的民俗商业街", "ticket_price": 0, "category": "街区", "rating": 4.3, "location": {"longitude": 104.048538, "latitude": 30.643717}},
                ],
                "meals": [
                    {"type": "lunch", "name": "龙抄手（总府路店）", "estimated_cost": 40},
                    {"type": "dinner", "name": "蜀九香火锅", "estimated_cost": 100},
                ],
            },
            {
                "date": "", "day_index": 1,
                "description": "文化之旅：从武侯祠到杜甫草堂",
                "transportation": "地铁+公交",
                "accommodation": "春熙路/太古里区域酒店",
                "attractions": [
                    {"name": "武侯祠", "address": "成都市武侯区武侯祠大街231号", "visit_duration": 120, "description": "中国唯一的君臣合祀祠庙，三国文化圣地", "ticket_price": 50, "category": "历史", "rating": 4.6, "location": {"longitude": 104.048025, "latitude": 30.644436}},
                    {"name": "杜甫草堂", "address": "成都市青羊区青华路37号", "visit_duration": 90, "description": "诗圣杜甫流寓成都时的故居，园林清幽", "ticket_price": 50, "category": "历史", "rating": 4.5, "location": {"longitude": 104.033902, "latitude": 30.661401}},
                    {"name": "人民公园", "address": "成都市青羊区少城路12号", "visit_duration": 60, "description": "体验成都人的慢生活，鹤鸣茶社喝盖碗茶", "ticket_price": 0, "category": "公园", "rating": 4.4, "location": {"longitude": 104.057729, "latitude": 30.661483}},
                ],
                "meals": [
                    {"type": "lunch", "name": "陈麻婆豆腐（青华路店）", "estimated_cost": 50},
                    {"type": "dinner", "name": "马路边边麻辣烫", "estimated_cost": 60},
                ],
            },
            {
                "date": "", "day_index": 2,
                "description": "都江堰水利奇观与青城山问道",
                "transportation": "高铁+公交",
                "accommodation": "春熙路/太古里区域酒店",
                "attractions": [
                    {"name": "都江堰", "address": "成都市都江堰市灌口镇", "visit_duration": 180, "description": "世界文化遗产，两千年仍在使用的水利工程奇迹，鱼嘴分水堤、飞沙堰、宝瓶口三大核心", "ticket_price": 80, "category": "历史", "rating": 4.8, "location": {"longitude": 103.627513, "latitude": 31.005023}},
                    {"name": "青城山", "address": "成都市都江堰市青城山镇", "visit_duration": 180, "description": "道教名山，'青城天下幽'，前山问道后山看水", "ticket_price": 80, "category": "自然", "rating": 4.7, "location": {"longitude": 103.592946, "latitude": 30.904451}},
                ],
                "meals": [
                    {"type": "lunch", "name": "都江堰尤兔头", "estimated_cost": 50},
                    {"type": "dinner", "name": "建设路小吃街", "estimated_cost": 40},
                ],
            },
        ],
        "overall_suggestions": "1. 大熊猫基地建议早上8点前到达，下午熊猫基本睡觉\n2. 成都美食以辣为主，不吃辣记得提前说\n3. 地铁+共享单车是最佳出行组合\n4. 5月成都温暖，偶有小雨，带把伞\n5. 都江堰+青城山建议一天游览，高铁往返仅需30分钟\n6. 建设路小吃街是本地人最爱，推荐降龙爪爪、锅巴土豆",
    },
}


def get_template(city: str) -> dict | None:
    """获取城市模板，支持模糊匹配。"""
    if city in TEMPLATES:
        return TEMPLATES[city]
    for name in TEMPLATES:
        if city in name or name in city:
            return TEMPLATES[name]
    return None


def list_templates() -> list[str]:
    return list(TEMPLATES.keys())
