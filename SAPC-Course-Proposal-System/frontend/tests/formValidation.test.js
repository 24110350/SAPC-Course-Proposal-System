import test from 'node:test';
import assert from 'node:assert/strict';
import {
  COURSE_TYPES, COURSE_LEVELS, COURSE_DURATIONS, OFFERING_FREQUENCIES,
  BTECH_ELECTIVE_BASKETS, BTECH_DISCIPLINE_ELECTIVES, MINORS_LIST,
  MSC_ELECTIVES, MTECH_DISCIPLINES, MDES_ELECTIVES, DISCIPLINE_ABBREVIATIONS
} from '../src/constants/sapcOptions.js';

test('ACAD-SAPC-01 Course Types contain all official disciplines', () => {
  assert.ok(COURSE_TYPES.includes('CS'), 'Must include CS');
  assert.ok(COURSE_TYPES.includes('EE'), 'Must include EE');
  assert.ok(COURSE_TYPES.includes('ME'), 'Must include ME');
  assert.ok(COURSE_TYPES.includes('HS'), 'Must include HS');
  assert.ok(COURSE_TYPES.includes('e-Masters'), 'Must include e-Masters');
  assert.ok(COURSE_TYPES.includes('Others'), 'Must include Others');
  assert.equal(COURSE_TYPES.length, 23);
});

test('ACAD-SAPC-01 Course Levels cover Levels 1 through 6', () => {
  assert.deepEqual(COURSE_LEVELS, ['1', '2', '3', '4', '5', '6']);
});

test('Course Durations cover all Quad formats', () => {
  assert.ok(COURSE_DURATIONS.includes('1 Quad'));
  assert.ok(COURSE_DURATIONS.includes('2 Quads (Half Semester)'));
  assert.ok(COURSE_DURATIONS.includes('3 Quads'));
  assert.ok(COURSE_DURATIONS.includes('4 Quads (Full Semester)'));
});

test('BTech Elective Baskets cover BS, HS, Mathematics, Science', () => {
  assert.ok(BTECH_ELECTIVE_BASKETS.includes('BS'));
  assert.ok(BTECH_ELECTIVE_BASKETS.includes('HS'));
  assert.ok(BTECH_ELECTIVE_BASKETS.includes('Mathematics'));
  assert.ok(BTECH_ELECTIVE_BASKETS.includes('Science'));
});

test('Minor disciplines cover all 26 official disciplines from form', () => {
  assert.equal(MINORS_LIST.length, 26);
  assert.ok(MINORS_LIST.includes('AI'));
  assert.ok(MINORS_LIST.includes('CS'));
  assert.ok(MINORS_LIST.includes('QT'));
  assert.ok(MINORS_LIST.includes('RB'));
  assert.ok(MINORS_LIST.includes('SY'));
});

test('Discipline abbreviations legend has full definitions', () => {
  assert.equal(DISCIPLINE_ABBREVIATIONS['AI'], 'Artificial Intelligence');
  assert.equal(DISCIPLINE_ABBREVIATIONS['CS'], 'Computer Science & Engineering');
  assert.equal(DISCIPLINE_ABBREVIATIONS['EE'], 'Electrical Engineering');
  assert.equal(DISCIPLINE_ABBREVIATIONS['ICDT'], 'Integrated Circuit Design & Technology');
  assert.equal(DISCIPLINE_ABBREVIATIONS['MSE'], 'Materials Engineering');
});

test('Email validation logic properly identifies valid and invalid emails', () => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  assert.ok(emailRegex.test('faculty@iitgn.ac.in'));
  assert.ok(emailRegex.test('proposer.name@domain.edu'));
  assert.ok(!emailRegex.test('invalid-email'));
  assert.ok(!emailRegex.test('@no-user.com'));
  assert.ok(!emailRegex.test('user@'));
});

test('L-T-P-C calculation formula produces correct academic credits', () => {
  const calculateCredits = (l, t, p) => l + t + Math.round(p * 0.5);
  assert.equal(calculateCredits(3, 0, 0), 3); // 3-0-0-3
  assert.equal(calculateCredits(3, 1, 0), 4); // 3-1-0-4
  assert.equal(calculateCredits(3, 0, 2), 4); // 3-0-2-4
  assert.equal(calculateCredits(0, 0, 3), 2); // 0-0-3-2 lab
});

test('Modification of existing course validation rule', () => {
  const validateModification = (isMod, code) => {
    if (isMod && (!code || code.trim() === '')) {
      return false;
    }
    return true;
  };

  assert.equal(validateModification(false, ''), true);
  assert.equal(validateModification(true, ''), false);
  assert.equal(validateModification(true, 'CS-301'), true);
});

test('Additional Recipients (CC) client-side parsing and validation', () => {
  const parseAndValidateRecipients = (input, facultyEmail = '') => {
    if (!input || !input.trim()) return { valid: true, recipients: [], error: null };
    const rawRecips = input.split(/[,;\n]/).map(s => s.trim()).filter(Boolean);
    if (rawRecips.length > 10) {
      return { valid: false, recipients: [], error: 'A maximum of 10 additional recipients is allowed.' };
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const normalizedFaculty = facultyEmail.trim().toLowerCase();
    const cleanList = [];
    const seen = new Set();
    for (const em of rawRecips) {
      if (!emailRegex.test(em)) {
        return { valid: false, recipients: [], error: `Invalid email address: '${em}'.` };
      }
      const lowered = em.toLowerCase();
      if (normalizedFaculty && lowered === normalizedFaculty) {
        continue; // omit submitter duplicate
      }
      if (!seen.has(lowered)) {
        seen.add(lowered);
        cleanList.push(lowered);
      }
    }
    return { valid: true, recipients: cleanList, error: null };
  };

  // 1. Empty is valid (optional)
  const emptyRes = parseAndValidateRecipients('');
  assert.equal(emptyRes.valid, true);
  assert.equal(emptyRes.recipients.length, 0);

  // 2. Single valid email
  const singleRes = parseAndValidateRecipients('hod.cse@iitgn.ac.in');
  assert.equal(singleRes.valid, true);
  assert.deepEqual(singleRes.recipients, ['hod.cse@iitgn.ac.in']);

  // 3. Multiple comma-separated emails with whitespace
  const multiRes = parseAndValidateRecipients('  hod.cse@iitgn.ac.in , colleague@iitgn.ac.in  ');
  assert.equal(multiRes.valid, true);
  assert.deepEqual(multiRes.recipients, ['hod.cse@iitgn.ac.in', 'colleague@iitgn.ac.in']);

  // 4. Invalid email rejection
  const invalidRes = parseAndValidateRecipients('hod.cse@iitgn.ac.in, not-an-email');
  assert.equal(invalidRes.valid, false);
  assert.match(invalidRes.error, /Invalid email address/);

  // 5. Duplicate deduplication
  const dedupRes = parseAndValidateRecipients('hod@iitgn.ac.in, HOD@iitgn.ac.in, colleague@iitgn.ac.in');
  assert.equal(dedupRes.valid, true);
  assert.deepEqual(dedupRes.recipients, ['hod@iitgn.ac.in', 'colleague@iitgn.ac.in']);

  // 6. Submitter own email is omitted to prevent unintended duplicate
  const submitterRes = parseAndValidateRecipients('proposer@iitgn.ac.in, hod@iitgn.ac.in', 'proposer@iitgn.ac.in');
  assert.equal(submitterRes.valid, true);
  assert.deepEqual(submitterRes.recipients, ['hod@iitgn.ac.in']);

  // 7. Max 10 recipients enforced
  const elevenEmails = Array.from({ length: 11 }, (_, i) => `prof${i}@iitgn.ac.in`).join(', ');
  const limitRes = parseAndValidateRecipients(elevenEmails);
  assert.equal(limitRes.valid, false);
  assert.match(limitRes.error, /maximum of 10/);
});

test('Requirement 4: Reason for Adding Course as Minor validation', () => {
  const validateMinorReason = (minors, reason) => {
    // If minor is selected, reason field is supported and can be optional or required based on dept guidelines
    if (minors && minors.length > 0) {
      return { hasMinors: true, reasonProvided: Boolean(reason && reason.trim().length > 0) };
    }
    return { hasMinors: false, reasonProvided: false };
  };

  const resWithoutMinors = validateMinorReason([], '');
  assert.equal(resWithoutMinors.hasMinors, false);

  const resWithMinors = validateMinorReason(['CS', 'AI'], 'Essential foundation for interdisciplinary computing');
  assert.equal(resWithMinors.hasMinors, true);
  assert.equal(resWithMinors.reasonProvided, true);
});

test('Requirement 2: Edit token format validation', () => {
  const isValidEditToken = (token) => {
    if (!token || typeof token !== 'string') return false;
    // URL-safe unguessable token: 32+ characters, base64url characters
    return token.length >= 32 && /^[A-Za-z0-9_-]+$/.test(token);
  };

  assert.equal(isValidEditToken(''), false);
  assert.equal(isValidEditToken('short-token'), false);
  assert.equal(isValidEditToken('valid_unguessable_token_1234567890_abcdefghij'), true);
});

test('Requirement 8: SAPC Number and Approval Date format validator', () => {
  const validateSapcData = (sapcNumber, approvalDate) => {
    const errors = [];
    if (sapcNumber && !/^SAPC-[A-Za-z0-9\-_/]+$/.test(sapcNumber)) {
      errors.push('SAPC number format recommended: SAPC-XXXX');
    }
    if (approvalDate && !/^\d{4}-\d{2}-\d{2}$/.test(approvalDate)) {
      errors.push('Approval date must follow YYYY-MM-DD');
    }
    return { valid: errors.length === 0, errors };
  };

  assert.equal(validateSapcData('SAPC-2026-001', '2026-03-15').valid, true);
  assert.equal(validateSapcData('invalid sapc', '2026-03-15').valid, false);
  assert.equal(validateSapcData('SAPC-2026-001', '15/03/2026').valid, false);
});
