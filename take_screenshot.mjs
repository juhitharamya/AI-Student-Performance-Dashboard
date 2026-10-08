import puppeteer from 'puppeteer-core';

async function run() {
  console.log('Connecting to Chrome...');
  const browser = await puppeteer.connect({
    browserURL: 'http://127.0.0.1:9222',
    defaultViewport: { width: 1440, height: 900 }
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1.5 });

  // 1. Capture Login Page
  console.log('Capturing Login Page...');
  await page.goto('http://localhost:5173/', { waitUntil: 'networkidle2' });
  await page.evaluate(() => localStorage.clear());
  await page.reload({ waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: 'docs/login_page.png' });
  console.log('Saved docs/login_page.png');

  // 2. Faculty Dashboard
  console.log('Logging into Faculty Dashboard...');
  // Click Faculty button
  const facultyButtons = await page.$$('button');
  for (const btn of facultyButtons) {
    const text = await page.evaluate(el => el.innerText, btn);
    if (text.includes('Faculty')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 500));
  await page.type('input[type="email"]', 'sarah@university.edu');
  await page.type('input[type="password"]', 'faculty123');
  const submitBtn = await page.$('button[type="submit"]');
  if (submitBtn) await submitBtn.click();

  console.log('Waiting for Faculty page...');
  await page.waitForFunction(() => {
    return document.body.innerText.includes('Dashboard Overview') && !document.body.innerText.includes('Loading dashboard');
  }, { timeout: 15000 });
  await new Promise(r => setTimeout(r, 1500));

  // Select filters on Faculty Dashboard:
  console.log('Applying filters to Faculty Dashboard...');
  const selects = await page.$$('select');
  if (selects.length >= 5) {
    // Dept, Year, Section, Subject, Test
    await page.select('select:nth-of-type(1)', 'CSM').catch(() => {});
    await page.select('select:nth-of-type(2)', '3rd Year').catch(() => {});
    await page.select('select:nth-of-type(3)', 'Section A').catch(() => {});
  } else {
    // Check if custom dropdowns or standard selects are used
    const buttons = await page.$$('button');
    for (const b of buttons) {
      const text = await page.evaluate(el => el.innerText, b);
      if (text.trim() === 'View') {
        console.log('Clicking View button...');
        await b.click();
        break;
      }
    }
  }
  await new Promise(r => setTimeout(r, 3000));
  await page.screenshot({ path: 'docs/faculty_dashboard.png' });
  console.log('Saved docs/faculty_dashboard.png');

  // 3. Faculty Student Marks Tab
  console.log('Switching to Student Marks tab...');
  const sidebarButtons = await page.$$('button');
  for (const b of sidebarButtons) {
    const text = await page.evaluate(el => el.innerText, b);
    if (text.includes('Student Marks')) {
      await b.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 2500));
  await page.screenshot({ path: 'docs/faculty_student_marks.png' });
  console.log('Saved docs/faculty_student_marks.png');

  // 4. Student Dashboard
  console.log('Logging out and signing in as Student...');
  await page.evaluate(() => localStorage.clear());
  await page.goto('http://localhost:5173/', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 800));

  const roleBtns = await page.$$('button');
  for (const btn of roleBtns) {
    const text = await page.evaluate(el => el.innerText, btn);
    if (text.includes('Student')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 500));
  await page.type('input[type="email"]', 'alex@university.edu');
  await page.type('input[type="password"]', 'student123');
  const stuSubmit = await page.$('button[type="submit"]');
  if (stuSubmit) await stuSubmit.click();

  console.log('Waiting for Student Dashboard to finish loading...');
  // Wait until loading spinner disappears
  await page.waitForFunction(() => {
    const text = document.body.innerText;
    return !text.includes('Loading your dashboard') && (text.includes('CGPA') || text.includes('Overall Attendance') || text.includes('Subjects'));
  }, { timeout: 25000 });
  await new Promise(r => setTimeout(r, 3500)); // wait for recharts animations

  await page.screenshot({ path: 'docs/student_dashboard.png' });
  console.log('Saved docs/student_dashboard.png');

  await page.close();
  await browser.disconnect();
  console.log('All screenshots captured successfully!');
}

run().catch(err => {
  console.error('Error during screenshot capture:', err);
  process.exit(1);
});
