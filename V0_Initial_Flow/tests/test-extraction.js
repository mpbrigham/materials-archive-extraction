#!/usr/bin/env node

const fs = require('fs');
const https = require('https');
const path = require('path');

function loadEnv() {
    const envPath = path.join(__dirname, '..', '.env');
    if (!fs.existsSync(envPath)) {
        console.error('Error: .env file not found');
        process.exit(1);
    }
    
    const envContent = fs.readFileSync(envPath, 'utf8');
    envContent.split('\n').forEach(line => {
        if (line && !line.startsWith('#')) {
            const [key, ...valueParts] = line.split('=');
            if (key && valueParts.length > 0) {
                const value = valueParts.join('=').replace(/^['"]|['"]$/g, '');
                process.env[key.trim()] = value.trim();
            }
        }
    });
}

loadEnv();

const TEST_PDF = path.join(__dirname, 'sample_data', 'test_product_1.pdf');
const PROMPT_FILE = path.join(__dirname, '..', 'prompts', 'llm_extraction.txt');
const SCHEMA_FILE = path.join(__dirname, '..', '..', 'specs', 'MATERIALS_SCHEMA.json');

async function testExtraction() {
    try {
        if (!fs.existsSync(TEST_PDF)) {
            console.error(`Error: Test PDF not found at ${TEST_PDF}`);
            process.exit(1);
        }
        if (!fs.existsSync(PROMPT_FILE)) {
            console.error(`Error: Prompt file not found at ${PROMPT_FILE}`);
            process.exit(1);
        }
        if (!fs.existsSync(SCHEMA_FILE)) {
            console.error(`Error: Schema file not found at ${SCHEMA_FILE}`);
            process.exit(1);
        }
        
        const pdfData = fs.readFileSync(TEST_PDF).toString('base64');
        const prompt = fs.readFileSync(PROMPT_FILE, 'utf8');
        const schema = JSON.parse(fs.readFileSync(SCHEMA_FILE, 'utf8'));
        
        const apiKey = process.env.LLM_API_KEY;
        if (!apiKey) {
            console.error('Error: LLM_API_KEY not found in environment');
            process.exit(1);
        }
        
        const apiUrl = `${process.env.LLM_API_ENDPOINT}?key=${apiKey}`;
        
        const requestBody = {
            contents: [{
                parts: [
                    {
                        text: prompt
                    },
                    {
                        inline_data: {
                            mime_type: "application/pdf",
                            data: pdfData
                        }
                    }
                ]
            }],
            generationConfig: {
                temperature: 0.1,
                topK: 32,
                topP: 0.95,
                maxOutputTokens: 8192,
                responseMimeType: "application/json",
                responseSchema: schema
            }
        };
        
        const response = await new Promise((resolve, reject) => {
            const urlParts = new URL(apiUrl);
            const req = https.request({
                hostname: urlParts.hostname,
                path: urlParts.pathname + urlParts.search,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            }, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    try {
                        resolve(JSON.parse(data));
                    } catch (e) {
                        reject(new Error('Failed to parse API response'));
                    }
                });
            });
            
            req.on('error', reject);
            req.write(JSON.stringify(requestBody));
            req.end();
        });
        
        if (response.error) {
            console.error('API Error:', response.error);
            process.exit(1);
        }
        
        const extractedContent = response.candidates?.[0]?.content?.parts?.[0]?.text;
        if (!extractedContent) {
            console.error('Error: No content in API response');
            process.exit(1);
        }
        
        let extractedData;
        try {
            extractedData = JSON.parse(extractedContent);
        } catch (parseError) {
            console.log(extractedContent);
            process.exit(1);
        }
        
        console.log(JSON.stringify(extractedData, null, 2));
        
        const outputFile = path.join(__dirname, 'extraction-result.json');
        fs.writeFileSync(outputFile, JSON.stringify(extractedData, null, 2));
        
    } catch (error) {
        console.error('Test failed:', error.message);
        process.exit(1);
    }
}

testExtraction();
