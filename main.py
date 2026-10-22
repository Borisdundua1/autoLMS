from os import wait
from pathlib import Path
from playwright.sync_api import Browser, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeout
import time

with sync_playwright() as playwright:
    # launch a browser
    browser = playwright.chromium.launch_persistent_context(
        user_data_dir="./my_browser_profile", headless=False
    )

    # create a fresh page
    page = browser.pages[0] if browser.pages else browser.new_page()

    # visit the desired website
    page.goto("https://lms.kiu.edu.ge")

    # wait for lms button to appear on page an then click it
    page.wait_for_selector("a[href='#/lms']")
    page.locator("a[href='#/lms']").click()

    # wait before the neccessary elements load
    page.wait_for_selector(".course")

    # storing all the course buttons
    course_count = page.locator(".group-wrapper .course").count()

    for i in range(course_count):
        course = page.locator(".group-wrapper .course").nth(i)

        # Store course title and make directory using the name
        course_title = course.locator(".text").inner_text().replace("/", "_")
        course_dir = Path.home() / "lms_materials" / f"{course_title}"
        course_dir.mkdir(exist_ok=True, parents=True)

        # open the course
        course.click()
        groups = page.locator(".group-wrapper .course").all()

        for group in groups:
            # store group name and make directory in corresponding course directory
            group_title = group.locator(".text").inner_text().replace("/", "_")
            group_dir = (
                Path.home() / "lms_materials" / f"{course_title}" / f"{group_title}"
            )
            group_dir.mkdir(exist_ok=True, parents=True)

            group.click()

            # wait for tab header to load
            page.wait_for_selector("mat-tab-header")
            page.get_by_text("სასწავლო მასალა").click()

            page.wait_for_selector("app-lms-materials mat-accordion", state="attached")
            time.sleep(0.1)

            # wait for panels to load then store all of them
            if page.locator(".mat-accordion .mat-expansion-panel").count() != 0:
                print(page.locator("mat-accordion mat-expansion-panel").count())
                page.wait_for_selector("mat-expansion-panel", timeout=5000)
                panels = page.locator("mat-expansion-panel").all()

                # iterate over the panels
                for panel in reversed(panels):
                    # wait for panels to load properly and make directory in corresponding directory
                    panel_title = panel.locator("mat-panel-title").inner_text().strip()
                    while not panel_title:
                        time.sleep(0.1)
                        panel_title = (
                            panel.locator("mat-panel-title").inner_text().strip()
                        )
                    panel_dir = (
                        Path.home()
                        / "lms_materials"
                        / f"{course_title}"
                        / f"{group_title}"
                        / f"{panel_title}"
                    )
                    panel_dir.mkdir(exist_ok=True, parents=True)

                    panel.click()

                    while panel.locator("a").count() == 0:
                        time.sleep(0.1)

                    file_links = panel.locator("a").all()

                    for link in file_links:
                        file_name = link.inner_html().strip().replace("/", "_")
                        file_path = panel_dir / file_name

                        if file_path.exists():
                            print(f"      [Skipped] Already exists: {file_name}")
                            continue

                        try:
                            with page.expect_download() as download_info:
                                link.click()

                            download = download_info.value
                            download.save_as(file_path)
                            print(f"      [Downloaded]: {file_name}")

                        except Exception as e:
                            print(f"      [!] Failed {file_name}: {e}")
            else:
                print("I guess it's empty")
            page.go_back()
            course.click()
        page.go_back()
        page.wait_for_selector("a[href='#/lms']")
        page.locator("a[href='#/lms']").click()

    browser.close()
