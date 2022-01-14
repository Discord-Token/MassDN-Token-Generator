from capmonster_python import HCaptchaTask
from managers.configStreamer import getValue
from python_anticaptcha import AnticaptchaClient, HCaptchaTaskProxyless

class captchaManager:
    def getCaptcha():
        if getValue("solver") == "anticaptcha":
            return captchaManager.antiCaptcha()
        elif getValue("solver") == "capmonster":
            return captchaManager.capMonster()

    def antiCaptcha():
        client = AnticaptchaClient(getValue("api_key"))
        task = HCaptchaTaskProxyless("https://discord.com/", "f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34")
        job = client.createTask(task)
        job.join()
        return job.get_solution_response()

    def capMonster():
        solver = HCaptchaTask(getValue("api_key"))
        task_id = solver.create_task("https://discord.com/", "f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34")
        return solver.join_task_result(task_id).get("gRecaptchaResponse")
