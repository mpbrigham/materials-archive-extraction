#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { createTransport } = require('nodemailer');
const Imap = require('imap');
const { simpleParser } = require('mailparser');

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

function parseArgs() {
    return process.argv.includes('--to-file');
}

loadEnv();

const SAMPLE_DATA_DIR = path.join(__dirname, 'sample_data');
const TEST_PDFS = [
    { filename: 'test_product_1.pdf', path: path.join(SAMPLE_DATA_DIR, 'test_product_1.pdf') },
    { filename: 'test_product_2.pdf', path: path.join(SAMPLE_DATA_DIR, 'test_product_2.pdf') },
    { filename: 'test_truly_invalid.pdf', path: path.join(SAMPLE_DATA_DIR, 'test_truly_invalid.pdf') }
];
const WAIT_TIME = 90;
const CHECK_INTERVAL = 5;

async function clearMailbox() {
    return new Promise((resolve, reject) => {
        const imap = new Imap({
            user: process.env.EMAIL_USER_TEST,
            password: process.env.EMAIL_PASS,
            host: process.env.IMAP_HOST,
            port: parseInt(process.env.IMAP_PORT),
            tls: true,
            tlsOptions: { rejectUnauthorized: false }
        });
        
        imap.once('ready', () => {
            imap.openBox('INBOX', false, (err, box) => {
                if (err) {
                    reject(err);
                    return;
                }
                
                if (box.messages.total === 0) {
                    imap.end();
                    resolve(0);
                    return;
                }
                
                imap.addFlags('1:*', '\\Deleted', (err) => {
                    if (err) {
                        reject(err);
                        return;
                    }
                    
                    imap.expunge((err) => {
                        if (err) {
                            reject(err);
                            return;
                        }
                        
                        imap.end();
                        resolve(box.messages.total);
                    });
                });
            });
        });
        
        imap.once('error', reject);
        imap.connect();
    });
}

async function sendTestEmail() {
    const transporter = createTransport({
        host: process.env.SMTP_HOST,
        port: parseInt(process.env.SMTP_PORT),
        secure: true,
        auth: {
            user: process.env.EMAIL_USER_TEST,
            pass: process.env.EMAIL_PASS
        }
    });
    
    const attachments = [];
    for (const testPdf of TEST_PDFS) {
        if (!fs.existsSync(testPdf.path)) {
            console.error(`Error: Test PDF not found at ${testPdf.path}`);
            process.exit(1);
        }
        
        attachments.push({
            filename: testPdf.filename,
            path: testPdf.path
        });
    }
    
    const mailOptions = {
        from: process.env.EMAIL_USER_TEST,
        to: process.env.EMAIL_USER,
        subject: `Materials Multi-PDF Test - ${new Date().toISOString()}`,
        text: `This is a multi-PDF test email for the materials extraction pipeline.\n\nAttachments:\n${TEST_PDFS.map(pdf => `- ${pdf.filename}`).join('\n')}`,
        attachments: attachments
    };
    
    const info = await transporter.sendMail(mailOptions);
    return info.messageId;
}

async function checkForResponse(toFile) {
    return new Promise((resolve, reject) => {
        const imap = new Imap({
            user: process.env.EMAIL_USER_TEST,
            password: process.env.EMAIL_PASS,
            host: process.env.IMAP_HOST,
            port: parseInt(process.env.IMAP_PORT),
            tls: true,
            tlsOptions: { rejectUnauthorized: false }
        });
        
        imap.once('ready', () => {
            imap.openBox('INBOX', false, (err, box) => {
                if (err) {
                    reject(err);
                    return;
                }
                
                const searchCriteria = [
                    ['FROM', process.env.EMAIL_USER]
                ];
                
                imap.search(searchCriteria, (err, results) => {
                    if (err) {
                        reject(err);
                        return;
                    }
                    
                    if (results.length === 0) {
                        imap.end();
                        resolve(null);
                        return;
                    }
                    
                    const latestUid = results[results.length - 1];
                    const fetch = imap.fetch(latestUid, {
                        bodies: '',
                        markSeen: false
                    });
                    
                    fetch.on('message', (msg) => {
                        msg.on('body', (stream) => {
                            simpleParser(stream, (err, mail) => {
                                if (err) {
                                    reject(err);
                                    return;
                                }
                                
                                console.log(`Subject: "${mail.subject}"`);
                                
                                if (mail.subject && (mail.subject.includes('Materials Extraction Complete') || mail.subject.includes('Materials Extraction Failed'))) {
                                    
                                    const fullEmail = `From: ${mail.from?.text}\nSubject: ${mail.subject}\nDate: ${mail.date}\n\n${mail.html || mail.text || 'No content'}`;
                                    
                                    if (toFile) {
                                        const outputPath = path.join(__dirname, 'latest_email.txt');
                                        fs.writeFileSync(outputPath, fullEmail);
                                        console.log(`Email saved to: ${outputPath}`);
                                    } else {
                                        console.log(fullEmail);
                                    }
                                    
                                    // Email processed successfully, close connection
                                    imap.end();
                                    resolve(mail);
                                } else {
                                    imap.end();
                                    resolve(null);
                                }
                            });
                        });
                    });
                    
                    fetch.once('error', (err) => {
                        imap.end();
                        reject(err);
                    });
                });
            });
        });
        
        imap.once('error', (err) => {
            reject(err);
        });
        
        imap.connect();
    });
}

async function testEmailPipeline() {
    const toFile = parseArgs();
    
    try {
        await clearMailbox();
        console.log('Test email sent');
        const messageId = await sendTestEmail();
        
        let response = null;
        const startTime = Date.now();
        
        while (!response && (Date.now() - startTime) < WAIT_TIME * 1000) {
            await new Promise(resolve => setTimeout(resolve, CHECK_INTERVAL * 1000));
            response = await checkForResponse(toFile);
        }
        
        if (!response) {
            console.log('No response received within timeout period');
            process.exit(1);
        }
        
    } catch (error) {
        console.error('Test failed:', error.message);
        process.exit(1);
    }
}

try {
    require('nodemailer');
    require('imap');
    require('mailparser');
} catch (e) {
    console.error('Missing required modules. Please run:');
    console.error('npm install nodemailer imap mailparser');
    process.exit(1);
}

testEmailPipeline();
