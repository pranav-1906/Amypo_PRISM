const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');
const pixelmatch = require('pixelmatch');
const PNG = require('pngjs').PNG;

// IMPORT YOUR AI MODULE HERE
const { generateFeedback } = require('./index');

const args = process.argv.slice(2);
const mode = args[0]; // 'baseline' or 'eval'
const VIEWPORT = { width: 1366, height: 768 };

const EVAL_TIMEOUT = 15000; 
    const timeoutId = setTimeout(() => {
        console.error("Evaluation timed out! Possible infinite loop detected.");
        process.exit(1); 
    }, EVAL_TIMEOUT);

async function runEngine() {
    const browser = await puppeteer.launch({ 
        headless: "new",
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process'
        ] 
    });
    
    const page = await browser.newPage();
    await page.setViewport(VIEWPORT);

    await page.setRequestInterception(true);
    page.on('request', (req) => {
        const url = req.url();
if (req.isNavigationRequest() || url.includes('cdnjs.cloudflare.com') || 
            url.includes('cdn.jsdelivr.net') ||      // Modern Bootstrap uses this
            url.includes('unpkg.com') || 
            url.includes('cdn.tailwindcss.com') ||   // Tailwind
            url.includes('stackpath.bootstrapcdn.com') || // Older Bootstrap
            url.includes('maxcdn.bootstrapcdn.com') ||    // Older Bootstrap
            url.includes('fonts.googleapis.com') ||  // Web Fonts
            url.includes('fonts.gstatic.com')) {   
                req.continue();
        } else {
            req.abort();
        }
    });

    if (mode === 'baseline') {
        const questionId = args[1];
        const html = fs.readFileSync(args[2], 'utf8');
        const css = fs.readFileSync(args[3], 'utf8');
        const js = fs.readFileSync(args[4], 'utf8');

        await renderPage(page, html, css, js);
        const baselinePath = path.join(__dirname, `../workspace/baselines/${questionId}_baseline.png`);
        await page.screenshot({ path: baselinePath });
        
        console.log(JSON.stringify({ status: "success", baseline: baselinePath }));
        await browser.close();
        process.exit(0);

    } else if (mode === 'eval') {
        const subId = args[1];
        const questionId = args[2];
        const html = fs.readFileSync(args[3], 'utf8');
        const css = fs.readFileSync(args[4], 'utf8');
        const js = fs.readFileSync(args[5], 'utf8');
        const rubric = JSON.parse(fs.readFileSync(args[6], 'utf8'));

        const expectedPath = path.join(__dirname, `../workspace/baselines/${questionId}_baseline.png`);
        const actualPath = path.join(__dirname, `../static/eval_images/${subId}_actual.png`);
        const diffPath = path.join(__dirname, `../static/eval_images/${subId}_diff.png`);
        const resultJsonPath = path.join(__dirname, `../workspace/temp_submissions/${subId}_result.json`);

        await renderPage(page, html, css, js);

        let results = {
            evaluationRun: {
                submissionId: subId,
                maxMarks: rubric.rubric || { html: 20, css: 35, js: 35, visual: 10 },
                totalScore: 0,
                breakdown: { html: 0, css: 0, js: 0, visual: 0 },
                failedTests: []
            },
            artifacts: {
                diffPercentage: 0,
                expectedImagePath: `/workspace/baselines/${questionId}_baseline.png`,
                actualImagePath: `/static/eval_images/${subId}_actual.png`,
                diffImagePath: `/static/eval_images/${subId}_diff.png`
            }
        };

        // --- NEW: JS Interaction Tests --- 
        // Run BEFORE screenshot so visual changes via JS are captured
        let jsScore = results.evaluationRun.maxMarks.js;
        if (rubric.interactionTests) {
            for (let test of rubric.interactionTests) {
                try {
                    if (test.steps) {
                        for (let step of test.steps) {
                            if (step.action === 'type') {
                                await page.type(step.selector, step.value);
                            } else if (step.action === 'click') {
                                await page.click(step.selector);
                            }
                            await new Promise(r => setTimeout(r, 100)); // UI delay
                        }
                    }

                    if (test.assertions) {
                        for (let assertion of test.assertions) {
                            const passed = await page.evaluate((assert) => {
                                if (assert.type === 'countEquals') {
                                    return document.querySelectorAll(assert.selector).length === assert.value;
                                }
                                const el = document.querySelector(assert.selector);
                                if (!el) return false;
                                if (assert.type === 'textContains') {
                                    return el.innerText.includes(assert.value);
                                }
                                return false;
                            }, assertion);
                            if (!passed) throw new Error("JS Assertion Failed");
                        }
                    }
                } catch (e) {
                    const weight = Number(test.weight) || 0; // Fixed math bug
                    jsScore -= weight;
                    results.evaluationRun.failedTests.push({
                        id: test.id, type: 'js', hint: test.failHint || "Interaction test failed."
                    });
                }
            }
        }
        results.evaluationRun.breakdown.js = Math.max(0, jsScore);

        // Take screenshot AFTER interactions are done
        await page.screenshot({ path: actualPath });

        // --- 1. DOM Tests ---
        let domScore = results.evaluationRun.maxMarks.html;
        if (rubric.domTests) {
            for (let test of rubric.domTests) {
                try {
                    const passed = await page.evaluate((selector, assert) => {
                        const elCount = document.querySelectorAll(selector).length;
                        if (assert.includes('count>=')) return elCount >= parseInt(assert.split('>=')[1]);
                        if (assert.includes('count==')) return elCount === parseInt(assert.split('==')[1]);
                        if (assert === 'exists') return elCount > 0;
                        return false;
                    }, test.selector, test.assert);

                    if (!passed) throw new Error("Assertion failed");
                } catch (e) {
                    const weight = Number(test.weight) || 0; // Fixed math bug
                    domScore -= weight;
                    results.evaluationRun.failedTests.push({
                        id: test.id, type: 'html', expected: test.assert, actual: "Failed/Missing", hint: test.failHint
                    });
                }
            }
        }
        results.evaluationRun.breakdown.html = Math.max(0, domScore);

        // --- 2. CSS Computed Style Tests ---
        let styleScore = results.evaluationRun.maxMarks.css;
        if (rubric.styleTests) {
            for (let test of rubric.styleTests) {
                try {
                    const actualStyle = await page.evaluate((selector, prop) => {
                        const el = document.querySelector(selector);
                        return el ? window.getComputedStyle(el)[prop] : null;
                    }, test.selector, test.property);

                    if (actualStyle !== test.expect) {
                        const weight = Number(test.weight) || 0; // Fixed math bug
                        styleScore -= weight;
                        results.evaluationRun.failedTests.push({
                            id: test.id, type: 'style', expected: test.expect, actual: actualStyle || 'null', hint: test.failHint
                        });
                    }
                } catch (e) {
                    const weight = Number(test.weight) || 0;
                    styleScore -= weight;
                    results.evaluationRun.failedTests.push({ id: test.id, type: 'style', hint: `Element ${test.selector} not found for CSS check.` });
                }
            }
        }
        results.evaluationRun.breakdown.css = Math.max(0, styleScore);

        // --- 3. Visual Tests ---
        let visualScore = results.evaluationRun.maxMarks.visual;
        
        if (fs.existsSync(expectedPath) && fs.existsSync(actualPath)) {
            const expectedImg = PNG.sync.read(fs.readFileSync(expectedPath));
            const actualImg = PNG.sync.read(fs.readFileSync(actualPath));
            const { width, height } = expectedImg;
            const diffImg = new PNG({ width, height });

            const numDiffPixels = pixelmatch(
                expectedImg.data, actualImg.data, diffImg.data, width, height, { threshold: 0.1 }
            );
            
            fs.writeFileSync(diffPath, PNG.sync.write(diffImg));

            const totalPixels = width * height;
            const diffPercentage = (numDiffPixels / totalPixels) * 100;
            results.artifacts.diffPercentage = diffPercentage;

            if (diffPercentage <= 1.0) {
                visualScore = visualScore * 1.0; 
            } else if (diffPercentage <= 3.0) {
                visualScore = visualScore * 0.8; 
                results.evaluationRun.failedTests.push({ id: 'vis', type: 'visual', hint: `Minor visual differences (${diffPercentage.toFixed(1)}%). Check alignment.` });
            } else if (diffPercentage <= 6.0) {
                visualScore = visualScore * 0.5; 
                results.evaluationRun.failedTests.push({ id: 'vis', type: 'visual', hint: `Moderate visual differences (${diffPercentage.toFixed(1)}%). Check layout structure.` });
            } else {
                visualScore = 0; 
                results.evaluationRun.failedTests.push({ id: 'vis', type: 'visual', hint: `Major visual differences (${diffPercentage.toFixed(1)}%). Layout fails to match baseline.` });
            }
        } else {
            visualScore = 0;
            results.evaluationRun.failedTests.push({ id: 'vis', type: 'visual', hint: "System error: Missing baseline or actual image." });
        }
        
        results.evaluationRun.breakdown.visual = Math.round(visualScore);

        // Update Total Score to include JS!
        results.evaluationRun.totalScore = results.evaluationRun.breakdown.html + results.evaluationRun.breakdown.css + results.evaluationRun.breakdown.js + results.evaluationRun.breakdown.visual;

        // --- 4. INTEGRATE GEMINI AI FEEDBACK ---
        try {
            if (results.artifacts.diffPercentage > 1.0 && fs.existsSync(expectedPath) && fs.existsSync(actualPath)) {
                const aiResponse = await generateFeedback(actualPath, expectedPath);
                results.aiFeedback = aiResponse;
            } else {
                results.aiFeedback = {
                    correct_elements: ["Perfect pixel match!"],
                    incorrect_elements: [],
                    improvement_suggestions: ["Great job, no visual improvements needed."]
                };
            }
        } catch (aiErr) {
            console.error("AI Feedback Failed:", aiErr.message);
            results.aiFeedback = null; 
        }

        fs.writeFileSync(resultJsonPath, JSON.stringify(results, null, 2));
        console.log(JSON.stringify({ status: "success", score: results.evaluationRun.totalScore }));
        
        await browser.close();
        process.exit(0);
    }
}

async function renderPage(page, html, css, js) {
    const combinedContent = `
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { margin: 0; padding: 0; box-sizing: border-box; }
                ${css}
            </style>
        </head>
        <body>
            ${html}
            <script>${js}</script>
        </body>
        </html>
    `;
    await page.setContent(combinedContent, { waitUntil: 'networkidle0', timeout: 0 });
    await page.addStyleTag({ 
        content: '*, *::before, *::after { transition: none !important; animation: none !important; caret-color: transparent !important; }' 
    });
    await new Promise(r => setTimeout(r, 1000));
}

runEngine().catch(err => {
    console.error(err);
    process.exit(1);
});