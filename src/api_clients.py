"""
API客户端，用于获取shortlinetv和reelshort的视频信息
"""
import re
import requests
from typing import List, Dict, Optional
import logging
# 使用绝对导入，兼容打包后的exe
try:
    from src.config import config
except ImportError:
    from .config import config

logger = logging.getLogger(__name__)


class ShortLineTVClient:
    """ShortLineTV API客户端"""
    
    API_URL = "https://shortlinetv.com/api/frontend/video/episode"
    
    HEADERS = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "access-channel": "direct",
        "access-token": "a43e0c88aecd58a662ee20fc119efdba",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "lang-id": "1",
        "origin": "https://shortlinetv.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "uid-token": "906508511232",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }
    
    COOKIES = {
        "PC_AC_ACCESS_TOKEN": "a43e0c88aecd58a662ee20fc119efdba",
        "AC_TOKEN": "AJUEDYDaNzIuK0tXBB2ry65eqN7Tn280",
        "pc_ga_utm": "{}",
        "__cf_bm": "7SEzu6x9MGo643kfcy_Rm3eRKEChUYl9E_I3JvXj1MQ-1764500722-1.0.1.1-cUZ72NdmDl3aVZE9Laca9EJWNMga5pPWGvjxkFd5GTSE180troyjW7Dn4_9drOqeUJm1qwSFcveUPUjiiIf_wtQCeFhziAnFYg5DtUakuLk"
    }
    
    @staticmethod
    def extract_video_id(url: str) -> Optional[int]:
        """从URL中提取video_id"""
        match = re.search(r'/videos/(\d+)', url)
        if match:
            return int(match.group(1))
        return None
    
    def get_episodes(self, video_id: int) -> Dict:
        """获取所有剧集信息"""
        try:
            payload = {
                "video_id": str(video_id),
                "episode_num": "1"
            }
            
            response = requests.post(
                self.API_URL,
                headers=self.HEADERS,
                cookies=self.COOKIES,
                json=payload,
                timeout=config.API_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == 0 and "data" in data:
                return data["data"]
            else:
                raise Exception(f"API返回错误: {data.get('msg', '未知错误')}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"请求shortlinetv API失败: {e}")
            raise Exception(f"获取剧集信息失败: {str(e)}")
    
    def parse_episodes(self, api_data: Dict, start_episode: int, end_episode: int, is_default_range: bool = False) -> List[Dict]:
        """解析剧集数据，返回指定区间的剧集列表
        
        注意：shortlinetv的episode_num从1开始
        - 如果is_default_range=True且start_episode=1且end_episode=0：下载所有剧集
        - 如果用户手动选择1-1：只下载第1集
        - 如果用户选择1-5：下载第1到第5集
        """
        episodes = []
        
        if "list" not in api_data or "episode_list" not in api_data["list"]:
            raise Exception("API数据格式错误：缺少episode_list")
        
        episode_list = api_data["list"]["episode_list"]
        drama_name = api_data["list"].get("title", "未知剧集")
        
        # 过滤指定区间的剧集（注意：episode_num从1开始）
        for episode in episode_list:
            episode_num = episode.get("episode_num", 0)
            
            # 判断是否下载所有剧集：只有默认值（start=1, end=0）且is_default_range=True时才下载所有
            if is_default_range and start_episode == 1 and end_episode == 0:
                # 下载所有剧集，不进行过滤
                pass
            elif start_episode == end_episode and start_episode > 0:
                # 下载指定的一集
                if episode_num != start_episode:
                    continue
            else:
                # 下载指定区间
                if start_episode > 0 and episode_num < start_episode:
                    continue
                if end_episode > 0 and episode_num > end_episode:
                    continue
            
            if "url" in episode:
                episodes.append({
                    "episode_num": episode_num,
                    "episode_name": f"{drama_name} - Episode {episode_num}",
                    "episode_url": f"https://shortlinetv.com/videos/{episode.get('video_id', '')}",
                    "download_url": episode["url"]
                })
        
        return sorted(episodes, key=lambda x: x["episode_num"])


class ReelShortClient:
    """ReelShort API客户端"""
    
    BASE_URL = "https://www.reelshort.com"
    
    HEADERS = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "purpose": "prefetch",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "x-nextjs-data": "1"
    }
    
    @staticmethod
    def extract_slug(url: str) -> Optional[str]:
        """从URL中提取slug"""
        # URL格式: https://www.reelshort.com/episodes/trailer-you-fired-a-fashion-icon-687f2a41314aed63020928f9-dr1wo1epdw
        # 或: https://www.reelshort.com/episodes/episode-1-you-fired-a-fashion-icon-687f2a41314aed63020928f9-6321c5n1u1
        # 需要提取: you-fired-a-fashion-icon-687f2a41314aed63020928f9
        
        # 先去掉查询参数
        url = url.split('?')[0]
        
        # 匹配 /episodes/ 后面的部分
        match = re.search(r'/episodes/[^/]+', url)
        if match:
            episode_part = match.group(0).replace('/episodes/', '')
            # 去掉开头的 trailer- 或 episode-X-
            episode_part = re.sub(r'^(trailer|episode-\d+)-', '', episode_part)
            # 去掉最后的 -chapter_id (chapter_id通常是10个字符左右)
            # slug格式: xxx-xxx-xxx-24位hex，最后是chapter_id
            # 尝试匹配: 前面是slug（包含24位hex），最后是短字符串（chapter_id）
            slug_match = re.search(r'^(.+?)-[a-z0-9]{8,12}$', episode_part)
            if slug_match:
                return slug_match.group(1)
            # 如果匹配失败，尝试更简单的模式：去掉最后一段
            parts = episode_part.split('-')
            if len(parts) > 1:
                # 假设最后一段是chapter_id，前面都是slug
                # 但slug的最后一部分应该是24位hex，所以需要保留它
                # 简单处理：如果最后一段很短（<15字符），可能是chapter_id
                if len(parts[-1]) < 15:
                    return '-'.join(parts[:-1])
                else:
                    return episode_part
        
        return None
    
    def get_movie_data(self, slug: str) -> Dict:
        """获取电影数据"""
        try:
            # 构建API URL
            api_url = f"{self.BASE_URL}/_next/data/6af1690/en/movie/{slug}.json"
            params = {"slug": slug}
            
            response = requests.get(
                api_url,
                headers=self.HEADERS,
                params=params,
                timeout=config.API_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            if "pageProps" in data and "data" in data["pageProps"]:
                return data["pageProps"]["data"]
            else:
                raise Exception("API返回数据格式错误")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"请求reelshort API失败: {e}")
            raise Exception(f"获取剧集信息失败: {str(e)}")
    
    def parse_episodes(self, api_data: Dict, slug: str, start_episode: int, end_episode: int, is_default_range: bool = False) -> List[Dict]:
        """解析剧集数据，返回指定区间的剧集列表
        
        注意：reelshort的serial_number从0开始，episode_num也对应从0开始
        - 如果is_default_range=True且start_episode=0且end_episode=0：下载所有剧集
        - 如果用户手动选择0-0：只下载第0集
        - 如果用户选择1-1：只下载第1集
        - 如果用户选择0-5：下载第0到第5集
        """
        episodes = []
        
        if "online_base" not in api_data:
            raise Exception("API数据格式错误：缺少online_base")
        
        drama_name = api_data.get("book_title", "未知剧集")
        online_base = api_data["online_base"]
        
        # reelshort的serial_number从0开始，episode_num也对应从0开始
        # 对于第0集，可能需要特殊处理（可能是trailer，chapter_type可能不是1）
        # 对于其他剧集，只处理正常剧集（chapter_type == 1），跳过预告片等（chapter_type == 2）
        for item in online_base:
            serial_number = item.get("serial_number", 0)
            chapter_id = item.get("chapter_id", "")
            chapter_type = item.get("chapter_type", 1)
            
            # reelshort的episode_num = serial_number（从0开始）
            episode_num = serial_number
            
            # 特殊处理：如果用户明确选择第0集，即使chapter_type不是1也要包含
            # 否则，只处理正常剧集（chapter_type == 1）
            is_target_episode_0 = (start_episode == 0 and end_episode == 0 and not is_default_range)
            if not is_target_episode_0 and chapter_type != 1:
                continue
            
            # 判断是否下载所有剧集：只有默认值（两个都是0）且is_default_range=True时才下载所有
            if is_default_range and start_episode == 0 and end_episode == 0:
                # 下载所有剧集，但只包含正常剧集（chapter_type == 1）
                if chapter_type != 1:
                    continue
            elif start_episode == end_episode:
                # 下载指定的一集（包括第0集）
                # 用户手动选择0-0时，只下载第0集（允许chapter_type不是1）
                if episode_num != start_episode:
                    continue
            else:
                # 下载指定区间
                if episode_num < start_episode:
                    continue
                if end_episode > 0 and episode_num > end_episode:
                    continue
                # 对于区间下载，只包含正常剧集
                if chapter_type != 1:
                    continue
            
            # 构建episode URL
            # 格式: https://www.reelshort.com/episodes/episode-{episode_num}-{slug}-{chapter_id}
            # 注意：URL中的episode_num需要+1，因为URL格式是episode-1, episode-2...
            # 但第0集对应的是trailer或episode-0，需要特殊处理
            if episode_num == 0:
                # 第0集可能是trailer，URL格式可能不同，需要检查实际URL格式
                # 根据用户提供的示例，第0集可能是trailer-xxx格式
                episode_url = f"{self.BASE_URL}/episodes/trailer-{slug}-{chapter_id}"
            else:
                episode_url = f"{self.BASE_URL}/episodes/episode-{episode_num}-{slug}-{chapter_id}"
            
            episodes.append({
                "episode_num": episode_num,  # 内部使用从0开始的编号
                "episode_name": f"{drama_name} - Episode {episode_num}",
                "episode_url": episode_url,
                "download_url": episode_url  # reelshort直接使用episode_url作为下载URL
            })
        
        return sorted(episodes, key=lambda x: x["episode_num"])

