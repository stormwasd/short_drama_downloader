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
    
    # 默认headers模板（如果未提供自定义token和uid，使用默认值）
    DEFAULT_HEADERS = {
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
    
    DEFAULT_COOKIES = {
        "PC_AC_ACCESS_TOKEN": "a43e0c88aecd58a662ee20fc119efdba",
        "AC_TOKEN": "AJUEDYDaNzIuK0tXBB2ry65eqN7Tn280",
        "pc_ga_utm": "{}",
        "__cf_bm": "7SEzu6x9MGo643kfcy_Rm3eRKEChUYl9E_I3JvXj1MQ-1764500722-1.0.1.1-cUZ72NdmDl3aVZE9Laca9EJWNMga5pPWGvjxkFd5GTSE180troyjW7Dn4_9drOqeUJm1qwSFcveUPUjiiIf_wtQCeFhziAnFYg5DtUakuLk"
    }
    
    def __init__(self, xtoken: str = None, uid: str = None):
        """初始化客户端
        
        Args:
            xtoken: access-token，用于替换headers中的access-token
            uid: uid-token，用于替换headers中的uid-token
        """
        # 构建headers，使用自定义token和uid（如果提供）
        self.HEADERS = self.DEFAULT_HEADERS.copy()
        if xtoken:
            self.HEADERS["access-token"] = xtoken
        if uid:
            self.HEADERS["uid-token"] = uid
        
        # 构建cookies，使用自定义token（如果提供）
        self.COOKIES = self.DEFAULT_COOKIES.copy()
        if xtoken:
            self.COOKIES["PC_AC_ACCESS_TOKEN"] = xtoken
    
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
    
    # 用于获取buildId的headers（与用户提供的curl命令一致）
    PAGE_HEADERS = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
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
    
    def get_build_id(self, drama_url: str) -> str:
        """从剧集页面HTML中提取buildId
        
        Args:
            drama_url: 剧集网址，例如: https://www.reelshort.com/episodes/trailer-xxx-xxx
            
        Returns:
            buildId字符串，例如: 7f1705b
            
        Raises:
            Exception: 如果无法获取或提取buildId
        """
        try:
            # 使用PAGE_HEADERS请求剧集页面
            response = requests.get(
                drama_url,
                headers=self.PAGE_HEADERS,
                timeout=config.API_TIMEOUT
            )
            response.raise_for_status()
            
            # 从HTML中提取buildId
            # 格式: "buildId":"7f1705b" 或 "buildId": "7f1705b"
            html_content = response.text
            build_id_pattern = r'"buildId"\s*:\s*"([^"]+)"'
            match = re.search(build_id_pattern, html_content)
            
            if match:
                build_id = match.group(1)
                logger.info(f"成功提取buildId: {build_id}")
                return build_id
            else:
                raise Exception("无法从页面HTML中提取buildId")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"请求reelshort页面失败: {e}")
            raise Exception(f"获取buildId失败: {str(e)}")
        except Exception as e:
            logger.error(f"提取buildId失败: {e}")
            raise Exception(f"提取buildId失败: {str(e)}")
    
    def get_movie_data(self, slug: str, drama_url: str = None, build_id: str = None) -> Dict:
        """获取电影数据
        
        Args:
            slug: 剧集slug
            drama_url: 剧集网址（用于获取buildId，如果build_id未提供）
            build_id: buildId（如果提供则直接使用，否则从drama_url获取）
            
        Returns:
            电影数据字典
        """
        try:
            # 如果没有提供build_id，则从drama_url获取
            if not build_id:
                if not drama_url:
                    raise Exception("需要提供drama_url或build_id")
                build_id = self.get_build_id(drama_url)
            
            # 构建API URL（使用动态获取的buildId）
            api_url = f"{self.BASE_URL}/_next/data/{build_id}/en/movie/{slug}.json"
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
            
            # 判断当前剧集是否在用户选择的区间内
            # 先进行区间判断，再进行chapter_type判断
            in_range = False
            is_target_episode_0 = (start_episode == 0 and end_episode == 0 and not is_default_range)
            
            if is_default_range and start_episode == 0 and end_episode == 0:
                # 下载所有剧集（默认值）
                in_range = True
            elif start_episode == end_episode:
                # 下载指定的一集
                in_range = (episode_num == start_episode)
            else:
                # 下载指定区间（包含边界）
                in_range = (start_episode <= episode_num <= end_episode)
            
            if not in_range:
                continue
            
            # 区间判断通过后，再进行chapter_type判断
            # 规则：
            # 1. 如果用户明确选择第0集（0-0且不是默认值），允许chapter_type不是1
            # 2. 如果区间包含第0集（start_episode == 0），且当前是第0集，允许chapter_type不是1
            # 3. 如果下载所有剧集（默认值），只包含正常剧集（chapter_type == 1）
            # 4. 其他情况，只包含正常剧集（chapter_type == 1）
            if is_default_range and start_episode == 0 and end_episode == 0:
                # 下载所有剧集，只包含正常剧集
                if chapter_type != 1:
                    continue
            else:
                # 非默认值的情况
                # 如果当前是第0集，且区间包含第0集，允许chapter_type不是1
                allow_non_type1 = (episode_num == 0 and start_episode == 0)
                if not allow_non_type1 and chapter_type != 1:
                    continue
            
            # 构建episode URL
            # 根据用户提供的示例和反馈：
            # - serial_number=0 (episode_num=0) → 第0集 → URL格式: trailer-xxx 或 episode-0-xxx
            # - serial_number=1 (episode_num=1) → 第1集 → URL格式: episode-1-xxx
            # - serial_number=2 (episode_num=2) → 第2集 → URL格式: episode-2-xxx
            # 所以URL中的编号 = episode_num（当episode_num > 0时）
            # 第0集使用trailer-xxx格式
            if episode_num == 0:
                # 第0集（trailer）使用trailer-xxx格式
                episode_url = f"{self.BASE_URL}/episodes/trailer-{slug}-{chapter_id}"
            else:
                # 其他剧集：URL中的编号 = episode_num
                # 例如：episode_num=1 → episode-1, episode_num=2 → episode-2
                episode_url = f"{self.BASE_URL}/episodes/episode-{episode_num}-{slug}-{chapter_id}"
            
            episodes.append({
                "episode_num": episode_num,  # 内部使用从0开始的编号
                "episode_name": f"{drama_name} - Episode {episode_num}",
                "episode_url": episode_url,
                "download_url": episode_url  # reelshort直接使用episode_url作为下载URL
            })
        
        return sorted(episodes, key=lambda x: x["episode_num"])

