const { chromium } = require('playwright');
const fs = require('fs');
require('dotenv').config();

const theaters = JSON.parse(process.env.THEATERS);

async function getScheduleInfo(venueName, url) {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    await page.goto(url);

    await page.evaluate(() => {
        let banner = document.querySelector('.cookie-consent');
        if (banner) banner.style.display = 'none';
    });

    let events = await page.evaluate(() => {
        let items = [];
        document.querySelectorAll('.schedule-block').forEach(block => {
            let date = block.getAttribute('id').replace('schedule', '');
            let title = block.querySelector('strong')?.innerText || '-';
            let times = block.querySelector('span')?.innerText.split('｜') || ['-', '-', '-'];
            let link = block.querySelector('.btns a:not(.is-pink)')?.href || '-';
            items.push({ date, title, openTime: times[0], startTime: times[1], endTime: times[2], link });
        });
        return items;
    });

    await browser.close();
    return events.map(event => ({ Venue: venueName, ...event }));
}

(async () => {
    let allEvents = [];
    for (const theater of theaters) {
        const events = await getScheduleInfo(theater.name, theater.url);
        allEvents.push(...events);
    }
    fs.writeFileSync('theater_schedules.json', JSON.stringify(allEvents, null, 2));
    console.log("Theater schedule data saved.");
})();
