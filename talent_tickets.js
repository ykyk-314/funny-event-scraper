const { chromium } = require('playwright');
const fs = require('fs');
require('dotenv').config();

const talentUrl = process.env.TALENT_BASE_URL;
const talents = JSON.parse(process.env.TALENTS);

async function getTicketInfo(talentId, talentName) {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    await page.goto(`${talentUrl}${talentId}`);

    // スケジュールデータ取得
    let events = await page.evaluate(() => {
        let items = [];
        document.querySelectorAll('#feed_ticket_info2 .feed-item-container').forEach(event => {
            let title = event.querySelector('.feed-ticket-title')?.innerText || '-';
            let date = event.querySelector('.opt-feed-ft-dateside p:first-child')?.innerText || '-';
            let time = event.querySelector('.opt-feed-ft-dateside p:last-child')?.innerText || '-';
            let members = event.querySelector('.opt-feed-ft-element-member')?.innerText.replace(/\n/g, '|') || '-';
            let venue = event.querySelector('.opt-feed-ft-element-venue')?.innerText || '-';
            let link = event.querySelector('.feed-item-link')?.href || '-';
            items.push({ title, date, time, members, venue, link });
        });
        return items;
    });

    await browser.close();
    return events.map(event => ({ TalentName: talentName, ...event }));
}

(async () => {
    let allEvents = [];
    for (const talent of talents) {
        const events = await getTicketInfo(talent.id, talent.name);
        allEvents.push(...events);
    }
    fs.writeFileSync('talent_tickets.json', JSON.stringify(allEvents, null, 2));
    console.log("Talent tickets data saved.");
})();
