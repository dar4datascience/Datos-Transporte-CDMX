const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  // Listen to console messages
  page.on('console', msg => console.log('BROWSER:', msg.text()));
  
  // Navigate to a blank page
  await page.goto('about:blank');
  
  // Test 1: Direct fetch (should fail with CORS)
  console.log('\n=== Test 1: Direct fetch to Organillero ===');
  const directResult = await page.evaluate(async () => {
    try {
      const response = await fetch('https://organillero.heliouz.com/api/realtime');
      const data = await response.json();
      return { success: true, vehicleCount: data.buses?.length || 0 };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });
  console.log('Direct fetch:', directResult);
  
  // Test 2: corsproxy.io
  console.log('\n=== Test 2: corsproxy.io ===');
  const corsproxyResult = await page.evaluate(async () => {
    try {
      const corsProxy = 'https://corsproxy.io/?';
      const apiUrl = 'https://organillero.heliouz.com/api/realtime';
      const response = await fetch(corsProxy + encodeURIComponent(apiUrl));
      const data = await response.json();
      return { success: true, vehicleCount: data.buses?.length || 0 };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });
  console.log('corsproxy.io:', corsproxyResult);
  
  // Test 3: allorigins.win
  console.log('\n=== Test 3: allorigins.win ===');
  const alloriginsResult = await page.evaluate(async () => {
    try {
      const corsProxy = 'https://api.allorigins.win/raw?url=';
      const apiUrl = 'https://organillero.heliouz.com/api/realtime';
      const response = await fetch(corsProxy + encodeURIComponent(apiUrl));
      const data = await response.json();
      return { success: true, vehicleCount: data.buses?.length || 0 };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });
  console.log('allorigins.win:', alloriginsResult);
  
  // Test 4: cors.sh
  console.log('\n=== Test 4: cors.sh ===');
  const corsshResult = await page.evaluate(async () => {
    try {
      const corsProxy = 'https://cors.sh/';
      const apiUrl = 'https://organillero.heliouz.com/api/realtime';
      const response = await fetch(corsProxy + apiUrl);
      const data = await response.json();
      return { success: true, vehicleCount: data.buses?.length || 0 };
    } catch (error) {
      return { success: false, error: error.message };
    }
  });
  console.log('cors.sh:', corsshResult);
  
  await browser.close();
})();
