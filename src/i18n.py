LANGUAGES = {"zh": "🇨🇳 中文", "en": "🇬🇧 English", "de": "🇩🇪 Deutsch", "fr": "🇫🇷 Français"}

TRANSLATIONS = {
    "app_title": {"zh": "酒店收益管理与智能调价助手", "en": "Hotel Revenue & Pricing Assistant", "de": "Hotel Revenue- und Preisassistent", "fr": "Assistant de revenu et de tarification hôtelière"},
    "app_caption": {"zh": "上传酒店订单数据，查看关键收益指标，并生成可解释的房价建议。", "en": "Upload hotel booking data, review revenue KPIs, and generate explainable room-price recommendations.", "de": "Laden Sie Hotelbuchungsdaten hoch, prüfen Sie Revenue-KPIs und erhalten Sie erklärbare Preisempfehlungen.", "fr": "Importez les données de réservation, suivez les indicateurs clés et générez des recommandations tarifaires explicables."},
    "language": {"zh": "语言", "en": "Language", "de": "Sprache", "fr": "Langue"},
    "configuration": {"zh": "配置", "en": "Configuration", "de": "Konfiguration", "fr": "Configuration"},
    "data": {"zh": "数据", "en": "Data", "de": "Daten", "fr": "Données"},
    "use_demo_data": {"zh": "使用内置演示数据", "en": "Use bundled demo data", "de": "Demo-Daten verwenden", "fr": "Utiliser les données de démonstration"},
    "recommendation_horizon": {"zh": "推荐周期", "en": "Recommendation horizon", "de": "Empfehlungszeitraum", "fr": "Horizon de recommandation"},
    "max_price_change": {"zh": "单次最大调价幅度", "en": "Max one-time price change", "de": "Maximale einmalige Preisänderung", "fr": "Variation tarifaire maximale"},
    "upload_hint": {"zh": "请上传三个 CSV 文件，或打开内置演示数据。", "en": "Upload all three CSV files or switch on bundled demo data.", "de": "Laden Sie alle drei CSV-Dateien hoch oder aktivieren Sie die Demo-Daten.", "fr": "Importez les trois fichiers CSV ou activez les données de démonstration."},
    "load_error": {"zh": "无法加载数据", "en": "Could not load data", "de": "Daten konnten nicht geladen werden", "fr": "Impossible de charger les données"},
    "validation_failed": {"zh": "数据校验失败。", "en": "Data validation failed.", "de": "Datenvalidierung fehlgeschlagen.", "fr": "Échec de la validation des données."},
    "sales_dashboard": {"zh": "销售看板", "en": "Sales Dashboard", "de": "Vertriebs-Dashboard", "fr": "Tableau de bord commercial"},
    "recommendations": {"zh": "调价建议", "en": "Recommendations", "de": "Empfehlungen", "fr": "Recommandations"},
    "data_preview": {"zh": "数据预览", "en": "Data Preview", "de": "Datenvorschau", "fr": "Aperçu des données"},
    "core_metrics": {"zh": "核心指标", "en": "Core Metrics", "de": "Kernkennzahlen", "fr": "Indicateurs clés"},
    "room_revenue": {"zh": "房费收入", "en": "Room Revenue", "de": "Zimmerumsatz", "fr": "Revenu chambres"},
    "occupancy": {"zh": "入住率", "en": "Occupancy", "de": "Auslastung", "fr": "Taux d’occupation"},
    "adr": {"zh": "平均房价", "en": "ADR", "de": "ADR", "fr": "ADR"},
    "revpar": {"zh": "RevPAR（可售房均收）", "en": "RevPAR", "de": "RevPAR", "fr": "RevPAR"},
    "summary_text": {"zh": "系统已根据历史订单、库存、当前价格和近期新增预订生成未来周期的人工复核调价建议。重点关注上调/下调日期、低置信度建议和临近入住日期的库存压力。", "en": "The system generated human-review pricing recommendations for the selected future horizon using historical bookings, inventory, current prices and recent pickup. Focus on price changes, low-confidence recommendations and inventory pressure close to arrival.", "de": "Das System hat für den gewählten Zeitraum Preisempfehlungen zur manuellen Prüfung auf Basis historischer Buchungen, Bestände, aktueller Preise und jüngstem Pickup erstellt. Achten Sie besonders auf Preisänderungen, Empfehlungen mit niedriger Sicherheit und kurzfristigen Bestandsdruck.", "fr": "Le système a généré des recommandations tarifaires à valider manuellement à partir des réservations historiques, des stocks, des prix actuels et du pickup récent. Priorité aux changements de prix, aux recommandations peu sûres et à la pression de stock proche de l’arrivée."},
    "pricing_actions": {"zh": "调价动作分布", "en": "Pricing Actions", "de": "Preisaktionen", "fr": "Actions tarifaires"},
    "top_opportunities": {"zh": "重点机会与风险", "en": "Top Opportunities & Risks", "de": "Wichtigste Chancen und Risiken", "fr": "Principales opportunités et risques"},
    "revpar_trend": {"zh": "每日 RevPAR 趋势", "en": "Daily RevPAR Trend", "de": "Täglicher RevPAR-Trend", "fr": "Tendance RevPAR quotidienne"},
    "avg_revpar_by_date": {"zh": "每日 RevPAR（每间可售房平均收入）", "en": "Average RevPAR by stay date", "de": "Durchschnittlicher RevPAR nach Aufenthaltstag", "fr": "RevPAR moyen par date de séjour"},
    "filter_actions": {"zh": "筛选动作", "en": "Filter actions", "de": "Aktionen filtern", "fr": "Filtrer les actions"},
    "filter_actions_help": {
        "zh": "按建议动作过滤推荐列表。\n\n🟢 上调：系统建议提高当前房价，预计可增加收益\n🔴 下调：系统建议降低房价，以提高未来售出间夜数\n🔵 保持：当前价格合理，无需调整\n\n可多选；不勾选则不显示任何结果。",
        "en": "Filter the recommendation list by suggested action.\n\n🟢 Increase: raise the current rate to capture more revenue\n🔴 Decrease: lower the rate to improve future sell-through\n🔵 Hold: current price is appropriate, no change needed\n\nMultiple selections allowed; deselecting all hides all rows.",
        "de": "Empfehlungsliste nach Aktion filtern.\n\n🟢 Erhöhen: Preis anheben für mehr Umsatz\n🔴 Senken: Preis senken für bessere Auslastung\n🔵 Halten: Aktueller Preis ist angemessen\n\nMehrfachauswahl möglich.",
        "fr": "Filtrer les recommandations par action suggérée.\n\n🟢 Augmenter: hausser le tarif pour accroître les revenus\n🔴 Baisser: réduire le tarif pour améliorer le taux d'occupation\n🔵 Maintenir: le prix actuel est approprié\n\nSélection multiple possible.",
    },
    "table_legend": {
        "zh": "🟢 上调 &nbsp;&nbsp; 🔴 下调 &nbsp;&nbsp; 🔵 保持 &nbsp;&nbsp; 红色边框 = 有风险提示，优先处理",
        "en": "🟢 Increase &nbsp;&nbsp; 🔴 Decrease &nbsp;&nbsp; 🔵 Hold &nbsp;&nbsp; Red border = risk flag, review first",
        "de": "🟢 Erhöhen &nbsp;&nbsp; 🔴 Senken &nbsp;&nbsp; 🔵 Halten &nbsp;&nbsp; Roter Rand = Risikohinweis",
        "fr": "🟢 Augmenter &nbsp;&nbsp; 🔴 Baisser &nbsp;&nbsp; 🔵 Maintenir &nbsp;&nbsp; Bordure rouge = alerte risque",
    },
    "download_excel": {"zh": "下载 Excel 报表", "en": "Download Excel report", "de": "Excel-Bericht herunterladen", "fr": "Télécharger le rapport Excel"},
    "bookings": {"zh": "订单", "en": "Bookings", "de": "Buchungen", "fr": "Réservations"},
    "inventory": {"zh": "库存", "en": "Inventory", "de": "Bestand", "fr": "Inventaire"},
    "current_prices": {"zh": "当前价格", "en": "Current prices", "de": "Aktuelle Preise", "fr": "Prix actuels"},
    "increase": {"zh": "上调", "en": "Increase", "de": "Erhöhen", "fr": "Augmenter"},
    "decrease": {"zh": "下调", "en": "Decrease", "de": "Senken", "fr": "Baisser"},
    "hold": {"zh": "保持", "en": "Hold", "de": "Halten", "fr": "Maintenir"},
    "high": {"zh": "高", "en": "High", "de": "Hoch", "fr": "Élevée"},
    "medium": {"zh": "中", "en": "Medium", "de": "Mittel", "fr": "Moyenne"},
    "low": {"zh": "低", "en": "Low", "de": "Niedrig", "fr": "Faible"},
    "price_change_count": {"zh": "需调价日期", "en": "Dates needing action", "de": "Tage mit Handlungsbedarf", "fr": "Dates nécessitant une action"},
    "high_confidence_count": {"zh": "高置信度建议", "en": "High-confidence recommendations", "de": "Empfehlungen mit hoher Sicherheit", "fr": "Recommandations à forte confiance"},
    "risk_count": {"zh": "风险提示", "en": "Risk flags", "de": "Risikohinweise", "fr": "Alertes de risque"},
    "chart_count": {"zh": "数量", "en": "Count", "de": "Anzahl", "fr": "Nombre"},
    "no_priority_items": {"zh": "当前周期没有明显的重点调价机会。", "en": "No major pricing opportunities in the selected horizon.", "de": "Keine wesentlichen Preisoptimierungschancen im gewählten Zeitraum.", "fr": "Aucune opportunité tarifaire majeure sur l’horizon sélectionné."},
    "recommendation_inventory_gap": {"zh": "有 {missing_count} 条当前价因为缺少对应库存或可售房间未生成推荐。请检查 inventory.csv 的入住日期和房型覆盖。", "en": "{missing_count} current-price rows were skipped because matching inventory or sellable rooms were missing. Check stay-date and room-type coverage in inventory.csv.", "de": "{missing_count} aktuelle Preiszeilen wurden übersprungen, weil passender Bestand oder verkaufbare Zimmer fehlen. Prüfen Sie Datum- und Zimmertyp-Abdeckung in inventory.csv.", "fr": "{missing_count} lignes de prix actuels ont été ignorées faute de stock ou de chambres vendables correspondants. Vérifiez les dates de séjour et types de chambre dans inventory.csv."},
    "column_stay_date": {"zh": "入住日期", "en": "Stay Date", "de": "Aufenthaltsdatum", "fr": "Date de séjour"},
    "column_hotel_id": {"zh": "酒店", "en": "Hotel", "de": "Hotel", "fr": "Hôtel"},
    "column_room_type": {"zh": "房型", "en": "Room Type", "de": "Zimmertyp", "fr": "Type de chambre"},
    "column_current_price": {"zh": "当前价", "en": "Current Price", "de": "Aktueller Preis", "fr": "Prix actuel"},
    "column_recommended_price": {"zh": "推荐价", "en": "Recommended Price", "de": "Empfohlener Preis", "fr": "Prix recommandé"},
    "column_price_floor": {"zh": "最低价", "en": "Price Floor", "de": "Mindestpreis", "fr": "Prix minimum"},
    "column_price_ceiling": {"zh": "最高价", "en": "Price Ceiling", "de": "Höchstpreis", "fr": "Prix maximum"},
    "column_action": {"zh": "建议动作", "en": "Action", "de": "Aktion", "fr": "Action"},
    "column_expected_revenue_delta": {"zh": "预计收益变化", "en": "Expected Revenue Delta", "de": "Erwartete Umsatzänderung", "fr": "Variation de revenu estimée"},
    "column_current_expected_revenue": {"zh": "当前价预期收益", "en": "Current Expected Revenue", "de": "Erwarteter Umsatz aktueller Preis", "fr": "Revenu attendu prix actuel"},
    "column_recommended_expected_revenue": {"zh": "推荐价预期收益", "en": "Recommended Expected Revenue", "de": "Erwarteter Umsatz empfohlener Preis", "fr": "Revenu attendu prix recommandé"},
    "column_demand_forecast_at_current_price": {"zh": "当前价需求预测", "en": "Demand Forecast at Current Price", "de": "Nachfrageprognose beim aktuellen Preis", "fr": "Prévision de demande au prix actuel"},
    "column_current_expected_sold_rooms": {"zh": "当前价预计售出", "en": "Current Expected Sold Rooms", "de": "Erwartete Verkäufe aktueller Preis", "fr": "Chambres attendues prix actuel"},
    "column_expected_sold_rooms": {"zh": "推荐价预计售出", "en": "Recommended Expected Sold Rooms", "de": "Erwartete Verkäufe empfohlener Preis", "fr": "Chambres attendues prix recommandé"},
    "column_expected_new_sold_rooms": {"zh": "预计新增售出", "en": "Expected New Sold Rooms", "de": "Erwartete neue Verkäufe", "fr": "Nouvelles ventes attendues"},
    "column_demand_elasticity": {"zh": "价格弹性", "en": "Price Elasticity", "de": "Preiselastizität", "fr": "Élasticité-prix"},
    "column_candidate_price_count": {"zh": "候选价数量", "en": "Candidate Price Count", "de": "Anzahl Kandidatenpreise", "fr": "Nombre de prix candidats"},
    "column_confidence": {"zh": "置信度", "en": "Confidence", "de": "Sicherheit", "fr": "Confiance"},
    "column_occupancy": {"zh": "入住率", "en": "Occupancy", "de": "Auslastung", "fr": "Occupation"},
    "column_remaining_inventory_ratio": {"zh": "剩余库存比例", "en": "Remaining Inventory Ratio", "de": "Restbestandsquote", "fr": "Ratio de stock restant"},
    "column_pickup_14d": {"zh": "14天新增预订", "en": "14-day Pickup", "de": "14-Tage-Pickup", "fr": "Pickup 14 jours"},
    "column_main_reasons": {"zh": "主要原因", "en": "Main Reasons", "de": "Hauptgründe", "fr": "Raisons principales"},
    "column_risk_flags": {"zh": "风险提示", "en": "Risk Flags", "de": "Risikohinweise", "fr": "Alertes de risque"},
}

ROOM_TYPES = {
    "Standard Double": {"zh": "标准大床房", "en": "Standard Double", "de": "Standard-Doppelzimmer", "fr": "Chambre double standard"},
    "Superior Double": {"zh": "高级大床房", "en": "Superior Double", "de": "Superior-Doppelzimmer", "fr": "Chambre double supérieure"},
    "Family Room": {"zh": "家庭房", "en": "Family Room", "de": "Familienzimmer", "fr": "Chambre familiale"},
}

REASONS = {
    "weekend demand pattern": {"zh": "周末需求较强", "en": "Weekend demand pattern", "de": "Wochenendnachfrage", "fr": "Demande de week-end"},
    "occupancy above similar historical dates": {"zh": "入住率高于历史类似日期", "en": "Occupancy above similar historical dates", "de": "Auslastung über ähnlichen historischen Tagen", "fr": "Occupation supérieure aux dates historiques similaires"},
    "occupancy below similar historical dates": {"zh": "入住率低于历史类似日期", "en": "Occupancy below similar historical dates", "de": "Auslastung unter ähnlichen historischen Tagen", "fr": "Occupation inférieure aux dates historiques similaires"},
    "recent 14-day pickup is strong": {"zh": "最近14天新增预订较强", "en": "Recent 14-day pickup is strong", "de": "Starker Pickup in den letzten 14 Tagen", "fr": "Pickup récent sur 14 jours élevé"},
    "weak recent pickup close to arrival": {"zh": "临近入住但近期新增预订偏弱", "en": "Weak recent pickup close to arrival", "de": "Schwacher Pickup kurz vor Anreise", "fr": "Pickup faible proche de l’arrivée"},
    "remaining inventory is limited": {"zh": "剩余库存有限", "en": "Remaining inventory is limited", "de": "Begrenzter Restbestand", "fr": "Stock restant limité"},
    "high remaining inventory close to arrival": {"zh": "临近入住但剩余库存较高", "en": "High remaining inventory close to arrival", "de": "Hoher Restbestand kurz vor Anreise", "fr": "Stock restant élevé proche de l’arrivée"},
    "no strong demand or inventory signal": {"zh": "暂无强需求或库存信号", "en": "No strong demand or inventory signal", "de": "Kein starkes Nachfrage- oder Bestandssignal", "fr": "Aucun signal fort de demande ou de stock"},
    "candidate price maximizes simulated expected revenue": {"zh": "候选价在收益模拟中预期收益最高", "en": "Candidate price maximizes simulated expected revenue", "de": "Kandidatenpreis maximiert simulierten erwarteten Umsatz", "fr": "Le prix candidat maximise le revenu attendu simulé"},
    "current price is near simulated revenue optimum": {"zh": "当前价已接近模拟收益最优点", "en": "Current price is near simulated revenue optimum", "de": "Aktueller Preis liegt nahe am simulierten Umsatzoptimum", "fr": "Le prix actuel est proche de l’optimum de revenu simulé"},
    "price elasticity model estimates demand response": {"zh": "价格弹性模型估计需求响应", "en": "Price elasticity model estimates demand response", "de": "Preiselastizitätsmodell schätzt Nachfragewirkung", "fr": "Le modèle d’élasticité-prix estime la réponse de la demande"},
}

RISKS = {
    "very close to stay date": {"zh": "非常接近入住日期", "en": "Very close to stay date", "de": "Sehr nah am Aufenthaltstag", "fr": "Très proche de la date de séjour"},
    "missing or invalid inventory": {"zh": "库存缺失或无效", "en": "Missing or invalid inventory", "de": "Fehlender oder ungültiger Bestand", "fr": "Stock manquant ou invalide"},
    "limited historical baseline": {"zh": "历史基准数据有限", "en": "Limited historical baseline", "de": "Begrenzte historische Basis", "fr": "Référence historique limitée"},
    "price floor applied": {"zh": "已应用最低价保护", "en": "Price floor applied", "de": "Mindestpreis angewendet", "fr": "Prix minimum appliqué"},
    "price ceiling applied": {"zh": "已应用最高价保护", "en": "Price ceiling applied", "de": "Höchstpreis angewendet", "fr": "Prix maximum appliqué"},
}

COLUMN_KEYS = {
    "stay_date": "column_stay_date", "hotel_id": "column_hotel_id", "room_type": "column_room_type",
    "current_price": "column_current_price", "recommended_price": "column_recommended_price",
    "price_floor": "column_price_floor", "price_ceiling": "column_price_ceiling",
    "action": "column_action", "expected_revenue_delta": "column_expected_revenue_delta",
    "current_expected_revenue": "column_current_expected_revenue", "recommended_expected_revenue": "column_recommended_expected_revenue",
    "demand_forecast_at_current_price": "column_demand_forecast_at_current_price",
    "current_expected_sold_rooms": "column_current_expected_sold_rooms", "expected_sold_rooms": "column_expected_sold_rooms",
    "expected_new_sold_rooms": "column_expected_new_sold_rooms", "demand_elasticity": "column_demand_elasticity",
    "candidate_price_count": "column_candidate_price_count", "confidence": "column_confidence",
    "occupancy": "column_occupancy", "remaining_inventory_ratio": "column_remaining_inventory_ratio", "pickup_14d": "column_pickup_14d",
    "main_reasons": "column_main_reasons", "risk_flags": "column_risk_flags",
}


def t(key: str, lang: str = "zh") -> str:
    return TRANSLATIONS.get(key, {}).get(lang) or TRANSLATIONS.get(key, {}).get("en") or key


def translate_value(value, lang: str = "zh"):
    return t(value, lang) if value in TRANSLATIONS else value


def translate_room_type(value, lang: str = "zh") -> str:
    return ROOM_TYPES.get(str(value), {}).get(lang) or ROOM_TYPES.get(str(value), {}).get("en") or value


def localize_room_type_values(df, lang: str = "zh"):
    localized = df.copy()
    if "room_type" in localized.columns:
        localized["room_type"] = localized["room_type"].map(lambda value: translate_room_type(value, lang))
    return localized


def translate_reason_list(text: str, lang: str = "zh") -> str:
    if not text:
        return ""
    parts = [part.strip() for part in str(text).split(";") if part.strip()]
    return "; ".join(REASONS.get(part, {}).get(lang, part) for part in parts)


def translate_risk_list(text: str, lang: str = "zh") -> str:
    if not text:
        return ""
    parts = [part.strip() for part in str(text).split(";") if part.strip()]
    return "; ".join(RISKS.get(part, {}).get(lang, part) for part in parts)


def localized_recommendations(df, lang: str = "zh"):
    localized = df.copy()
    if "room_type" in localized.columns:
        localized["room_type"] = localized["room_type"].map(lambda value: translate_room_type(value, lang))
    if "action" in localized.columns:
        localized["action"] = localized["action"].map(lambda value: translate_value(value, lang))
    if "confidence" in localized.columns:
        localized["confidence"] = localized["confidence"].map(lambda value: translate_value(value, lang))
    if "main_reasons" in localized.columns:
        localized["main_reasons"] = localized["main_reasons"].map(lambda value: translate_reason_list(value, lang))
    if "risk_flags" in localized.columns:
        localized["risk_flags"] = localized["risk_flags"].map(lambda value: translate_risk_list(value, lang))
    for col in ("occupancy", "remaining_inventory_ratio"):
        if col in localized.columns:
            localized[col] = localized[col].mul(100).round(2)
    return localized.rename(columns={column: t(key, lang) for column, key in COLUMN_KEYS.items() if column in localized.columns})
