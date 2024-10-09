from twocaptcha import TwoCaptcha


class CaptchaHandler:
    def __init__(self, api_key: str):
        self.solver = TwoCaptcha(apiKey=api_key, defaultTimeout=180)


    def solve_hcatpcha(self, site_key: str, r_data: str, proxy: str | None) -> str:
        if proxy is not None:
            type, uri = proxy.split("://")

            result = self.solver.hcaptcha(
                sitekey=site_key,
                url="https://discord.com/",
                invisible=1,
                data = r_data,
                proxy = {
                    "type": type,
                    "uri": uri
                }
            )
        
        else:
            result = self.solver.hcaptcha(
                sitekey=site_key,
                url="https://discord.com/",
                invisible=1,
                data = r_data
            )
        
        return result["code"]