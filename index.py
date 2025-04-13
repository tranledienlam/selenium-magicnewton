import argparse
import time
from selenium.webdriver.common.by import By

from browser_automation import BrowserManager, Node
from utils import Utility

class Setup:
    def __init__(self, node: Node, profile) -> None:
        self.node = node
        self.profile = profile
        
    def _run(self):
        self.node.go_to('https://www.magicnewton.com/portal/rewards')

class Auto:
    def __init__(self, node: Node, profile: dict) -> None:
        self.driver = node._driver
        self.node = node
        self.profile_name = profile.get('profile_name')
        self.email = profile.get('email')

    def roll_dice(self):
        self.node.find_and_click(By.CSS_SELECTOR, '[alt="newton"]')
        if not self.node.find_and_click(By.XPATH, '//p[contains(text(),"Roll now")]'):
            self.node.snapshot(f'{self.profile_name} không tìm thấy nút roll', False)
            return False
        # close all popup
        self.node.find_and_click(By.XPATH, '''//p[contains(text(), "Let's roll")]''', timeout=10)
        self.node.find_and_click(By.XPATH, '//p[contains(text(), "Throw Dice")]', timeout=10)
        if not self.node.find(By.XPATH, '//p[contains(text(), "Return Home")]'):
            self.node.snapshot(f'{self.profile_name} không tìm thấy nút Throw Dice', False)
            self.node.find_and_click(By.XPATH, '//p[contains(text(), "Return Home")]')
            return False
        else:
            self.node.snapshot(f'Hôm nay đã roll', False)
            return True
    def play_minesweeper(self):
        self.node.find_and_click(By.CSS_SELECTOR, '[alt="newton"]')
        js = '''
// ==UserScript==
// @name         Auto do min MagicNewton
// @namespace    http://tampermonkey.net/
// @version      1.1
// @description  da so thi dung dung, da dung thi dung so
// @author       caobang
// @match        https://www.magicnewton.com/portal/rewards
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    // Configuration
    const MOVE_DELAY = 500;      // Thời gian giữa các lần đi (ms)
    const SOLVE_DELAY = 3000;    // Thời gian chờ sau mỗi lần đi (ms)
    const RELOAD_DELAY = 10000;  // Thời gian chờ trước khi tải lại sau khi kết thúc game (10 giây)
    const DEBUG = true;          // Bật/tắt chế độ ghi log (debug)
    const MAX_FLAGS = 10;        // Số lượng cờ tối đa được phép
    const MIN_DELAY = 1000;
    const MAX_DELAY = 3000;

    let flagCount = 0;
    let actionQueue = [];

    function log(message) {
        if (DEBUG) console.log(`[Dân cày airdrop] ${message}`);
    }

    // Generate random delay between 1 and 3 seconds
    function randomDelay() {
        return new Promise(resolve => {
            const delay = Math.floor(Math.random() * (MAX_DELAY - MIN_DELAY + 1)) + MIN_DELAY;
            setTimeout(resolve, delay);
        });
    }

    async function triggerClick(element, isRightClick = false) {
        if (!element) return false;

        if (isRightClick && flagCount >= MAX_FLAGS) {
            log("Không thể đánh dấu: Đã đạt đến giới hạn đánh dấu tối đa (10)");
            return false;
        }

        if (isRightClick && element.classList.contains('tile-flagged')) {
            log("Ô đã được gắn cờ, bỏ qua hành động");
            return false;
        }

        const rect = element.getBoundingClientRect();
        const offsetX = Math.random() * rect.width * 0.8 + rect.width * 0.1;
        const offsetY = Math.random() * rect.height * 0.8 + rect.height * 0.1;
        const clickX = rect.left + offsetX;
        const clickY = rect.top + offsetY;

        log(`Thực hiện ${isRightClick ? 'right' : 'left'} click tại (${clickX.toFixed(2)}, ${clickY.toFixed(2)})`);

        const event = new MouseEvent(isRightClick ? 'contextmenu' : 'click', {
            bubbles: true,
            cancelable: true,
            clientX: clickX,
            clientY: clickY,
            view: window,
            button: isRightClick ? 2 : 0
        });

        const success = element.dispatchEvent(event);
        if (success && isRightClick) {
            await new Promise(resolve => setTimeout(resolve, 500));
            if (element.classList.contains('tile-flagged')) {
                flagCount++;
                log(`Đã đặt cờ thành công. Tổng số cờ: ${flagCount}/${MAX_FLAGS}`);
            } else {
                log("Gắn cờ thất bại, có thể giao diện chưa cập nhật");
                return false;
            }
        }
        return success;
    }

    async function processActionQueue() {
        while (actionQueue.length > 0) {
            const action = actionQueue.shift();
            await action();
            await randomDelay();
        }
    }

    function getGrid() {
        const tiles = document.querySelectorAll('.tile.jetbrains');
        if (tiles.length === 0) return null;

        const grid = [];
        let row = [];
        let width = 0;

        flagCount = 0;

        let prevY = null;
        tiles.forEach((tile, index) => {
            const rect = tile.getBoundingClientRect();
            if (prevY === null) {
                prevY = rect.y;
            } else if (rect.y !== prevY && width === 0) {
                width = index;
            }
            prevY = rect.y;
        });

        if (width === 0) width = 10;

        tiles.forEach((tile, index) => {
            const isFlagged = tile.classList.contains('tile-flagged');
            const isOpened = tile.classList.contains('tile-changed') ||
                             (tile.style.backgroundColor === 'transparent' &&
                              tile.style.border === 'none' &&
                              tile.style.boxShadow === 'none' &&
                              tile.style.color === 'white');

            if (isFlagged) flagCount++;

            let value = null;
            if (isOpened && !isFlagged) {
                const content = tile.textContent.trim();
                value = content ? parseInt(content) || 0 : 0;
            }

            row.push({
                element: tile,
                isOpened: isOpened,
                isFlagged: isFlagged,
                value: value,
                index: index
            });

            if ((index + 1) % width === 0) {
                grid.push(row);
                row = [];
            }
        });

        log(`Số cờ hiện tại: ${flagCount}/${MAX_FLAGS}`);
        return grid;
    }

    function getNeighbors(grid, x, y) {
        const neighbors = [];
        for (let i = -1; i <= 1; i++) {
            for (let j = -1; j <= 1; j++) {
                if (i === 0 && j === 0) continue;
                const newX = x + i;
                const newY = y + j;
                if (newX >= 0 && newX < grid.length && newY >= 0 && newY < grid[0].length) {
                    neighbors.push({ tile: grid[newX][newY], x: newX, y: newY });
                }
            }
        }
        return neighbors;
    }

    async function basicSolve(grid) {
        let actionTaken = false;

        for (let i = 0; i < grid.length; i++) {
            for (let j = 0; j < grid[i].length; j++) {
                const tile = grid[i][j];
                if (!tile.isOpened || tile.value === 0) continue;

                const neighbors = getNeighbors(grid, i, j);
                const unopenedNeighbors = neighbors.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
                const flaggedNeighbors = neighbors.filter(n => n.tile.isFlagged);

                if (tile.value - flaggedNeighbors.length === unopenedNeighbors.length && unopenedNeighbors.length > 0) {
                    unopenedNeighbors.forEach(n => {
                        if (!n.tile.isFlagged && flagCount < MAX_FLAGS) {
                            log(`Hàng đợi gắn cờ tại (${n.x}, ${n.y})`);
                            actionQueue.push(async () => {
                                const success = await await triggerClick(n.tile.element, true);
                                if (success) {
                                    n.tile.isFlagged = true;
                                }
                            });
                            actionTaken = true;
                        }
                    });
                }
                else if (tile.value === flaggedNeighbors.length && unopenedNeighbors.length > 0) {
                    unopenedNeighbors.forEach(n => {
                        log(`Hàng đợi mở ô tại (${n.x}, ${n.y})`);
                        actionQueue.push(async () => {
                            await triggerClick(n.tile.element);
                        });
                        actionTaken = true;
                    });
                }
            }
        }

        return actionTaken;
    }

    async function advancedPatternAnalysis(grid) {
        let actionTaken = false;

        actionTaken = actionTaken || await detect121Pattern(grid);
        actionTaken = actionTaken || await detect1221Pattern(grid);
        actionTaken = actionTaken || await detect123Pattern(grid);
        actionTaken = actionTaken || await detect1231Pattern(grid);
        actionTaken = actionTaken || await detect12321Pattern(grid);
        actionTaken = actionTaken || await detect242Pattern(grid);
        actionTaken = actionTaken || await detect424Pattern(grid);
        actionTaken = actionTaken || await detect245Pattern(grid);
        actionTaken = actionTaken || await detect454Pattern(grid);
        actionTaken = actionTaken || await performTankSolving(grid);

        return actionTaken;
    }

    function checkPattern(grid, startX, startY, endX, endY, pattern) {
        const dx = endX - startX === 0 ? 0 : (endX - startX) / Math.abs(endX - startX);
        const dy = endY - startY === 0 ? 0 : (endY - startY) / Math.abs(endY - startY);

        let x = startX;
        let y = startY;
        let patternIndex = 0;

        while ((dx === 0 || (dx > 0 ? x <= endX : x >= endX)) && (dy === 0 || (dy > 0 ? y <= endY : y >= endY))) {
            if (x < 0 || x >= grid.length || y < 0 || y >= grid[0].length) return false;
            const tile = grid[x][y];
            if (!tile.isOpened || tile.value !== pattern[patternIndex]) return false;

            x += dx;
            y += dy;
            patternIndex++;
        }

        return patternIndex === pattern.length;
    }

    async function detect121Pattern(grid) {
        let actionTaken = false;

        for (let i = 0; i < grid.length; i++) {
            for (let j = 0; j < grid[i].length - 2; j++) {
                if (checkPattern(grid, i, j, i, j+2, [1,2,1])) {
                    actionTaken = actionTaken || await solve121Pattern(grid, {x: i, y: j}, {x: i, y: j+1}, {x: i, y: j+2});
                }
            }
        }

        for (let i = 0; i < grid.length - 2; i++) {
            for (let j = 0; j < grid[i].length; j++) {
                if (checkPattern(grid, i, j, i+2, j, [1,2,1])) {
                    actionTaken = actionTaken || await solve121Pattern(grid, {x: i, y: j}, {x: i+1, y: j}, {x: i+2, y: j});
                }
            }
        }

        return actionTaken;
    }

    async function solve121Pattern(grid, one1, two, one2) {
        let actionTaken = false;

        const neighborsOne1 = getNeighbors(grid, one1.x, one1.y);
        const neighborsTwo = getNeighbors(grid, two.x, two.y);
        const neighborsOne2 = getNeighbors(grid, one2.x, one2.y);

        const flaggedOne1 = neighborsOne1.filter(n => n.tile.isFlagged).length;
        const flaggedTwo = neighborsTwo.filter(n => n.tile.isFlagged).length;
        const flaggedOne2 = neighborsOne2.filter(n => n.tile.isFlagged).length;

        const unopenedOne1 = neighborsOne1.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedTwo = neighborsTwo.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedOne2 = neighborsOne2.filter(n => !n.tile.isOpened && !n.tile.isFlagged);

        if (flaggedOne1 === 0 && flaggedTwo === 0 && flaggedOne2 === 0) {
            const commonNeighbors1 = unopenedOne1.filter(n1 => unopenedTwo.some(n2 => n1.x === n2.x && n1.y === n2.y));
            const commonNeighbors2 = unopenedOne2.filter(n1 => unopenedTwo.some(n2 => n1.x === n2.x && n1.y === n2.y));
            const uniqueNeighbors = unopenedTwo.filter(n =>
                !commonNeighbors1.some(cn => cn.x === n.x && cn.y === n.y) &&
                !commonNeighbors2.some(cn => cn.x === n.x && cn.y === n.y));

            if (uniqueNeighbors.length === 2 - flaggedTwo) {
                uniqueNeighbors.forEach(n => {
                    if (!n.tile.isFlagged && flagCount < MAX_FLAGS) {
                        log(`Hàng đợi gắn cờ tại (${n.x}, ${n.y}) dựa trên mẫu 1-2-1`);
                        actionQueue.push(async () => {
                            const success = await triggerClick(n.tile.element, true);
                            if (success) {
                                n.tile.isFlagged = true;
                            }
                        });
                        actionTaken = true;
                    }
                });
            }

            if (flaggedTwo + uniqueNeighbors.length === 2) {
                [...commonNeighbors1, ...commonNeighbors2].forEach(n => {
                    log(`Hàng đợi mở ô tại (${n.x}, ${n.y}) dựa trên mẫu 1-2-1`);
                    actionQueue.push(async () => {
                        await triggerClick(n.tile.element);
                    });
                    actionTaken = true;
                });
            }
        }

        return actionTaken;
    }

    async function detect1221Pattern(grid) {
        let actionTaken = false;

        for (let i = 0; i < grid.length; i++) {
            for (let j = 0; j < grid[i].length - 3; j++) {
                if (checkPattern(grid, i, j, i, j+3, [1,2,2,1])) {
                    actionTaken = actionTaken || await solve1221Pattern(grid, {x: i, y: j}, {x: i, y: j+1}, {x: i, y: j+2}, {x: i, y: j+3});
                }
            }
        }

        for (let i = 0; i < grid.length - 3; i++) {
            for (let j = 0; j < grid[i].length; j++) {
                if (checkPattern(grid, i, j, i+3, j, [1,2,2,1])) {
                    actionTaken = actionTaken || await solve1221Pattern(grid, {x: i, y: j}, {x: i+1, y: j}, {x: i+2, y: j}, {x: i+3, y: j});
                }
            }
        }

        return actionTaken;
    }

    async function solve1221Pattern(grid, one1, two1, two2, one2) {
        let actionTaken = false;

        const neighborsOne1 = getNeighbors(grid, one1.x, one1.y);
        const neighborsTwo1 = getNeighbors(grid, two1.x, two1.y);
        const neighborsTwo2 = getNeighbors(grid, two2.x, two2.y);
        const neighborsOne2 = getNeighbors(grid, one2.x, one2.y);

        const flaggedOne1 = neighborsOne1.filter(n => n.tile.isFlagged).length;
        const flaggedTwo1 = neighborsTwo1.filter(n => n.tile.isFlagged).length;
        const flaggedTwo2 = neighborsTwo2.filter(n => n.tile.isFlagged).length;
        const flaggedOne2 = neighborsOne2.filter(n => n.tile.isFlagged).length;

        const unopenedOne1 = neighborsOne1.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedTwo1 = neighborsTwo1.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedTwo2 = neighborsTwo2.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedOne2 = neighborsOne2.filter(n => !n.tile.isOpened && !n.tile.isFlagged);

        if (flaggedOne1 === 0 && flaggedTwo1 === 0 && flaggedTwo2 === 0 && flaggedOne2 === 0) {
            const sharedTwo1Two2 = unopenedTwo1.filter(n1 => unopenedTwo2.some(n2 => n1.x === n2.x && n1.y === n2.y));
            const uniqueTwo1 = unopenedTwo1.filter(n => !sharedTwo1Two2.some(s => s.x === n.x && s.y === n.y));
            const uniqueTwo2 = unopenedTwo2.filter(n => !sharedTwo1Two2.some(s => s.x === n.x && s.y === n.y));

            if (uniqueTwo1.length + sharedTwo1Two2.length === 2 && uniqueTwo2.length + sharedTwo1Two2.length === 2) {
                uniqueTwo1.concat(uniqueTwo2).forEach(n => {
                    if (!n.tile.isFlagged && flagCount < MAX_FLAGS) {
                        log(`Hàng đợi gắn cờ tại (${n.x}, ${n.y}) dựa trên mẫu 1-2-2-1`);
                        actionQueue.push(async () => {
                            const success = await triggerClick(n.tile.element, true);
                            if (success) {
                                n.tile.isFlagged = true;
                            }
                        });
                        actionTaken = true;
                    }
                });
            }
        }

        return actionTaken;
    }

    async function detect123Pattern(grid) {
        let actionTaken = false;

        for (let i = 0; i < grid.length; i++) {
            for (let j = 0; j < grid[i].length - 2; j++) {
                if (checkPattern(grid, i, j, i, j+2, [1,2,3])) {
                    actionTaken = actionTaken || await solve123Pattern(grid, {x: i, y: j}, {x: i, y: j+1}, {x: i, y: j+2});
                }
            }
        }

        for (let i = 0; i < grid.length - 2; i++) {
            for (let j = 0; j < grid[i].length; j++) {
                if (checkPattern(grid, i, j, i+2, j, [1,2,3])) {
                    actionTaken = actionTaken || await solve123Pattern(grid, {x: i, y: j}, {x: i+1, y: j}, {x: i+2, y: j});
                }
            }
        }

        return actionTaken;
    }

    async function solve123Pattern(grid, one, two, three) {
        let actionTaken = false;

        const neighborsOne = getNeighbors(grid, one.x, one.y);
        const neighborsTwo = getNeighbors(grid, two.x, two.y);
        const neighborsThree = getNeighbors(grid, three.x, three.y);

        const flaggedOne = neighborsOne.filter(n => n.tile.isFlagged).length;
        const flaggedTwo = neighborsTwo.filter(n => n.tile.isFlagged).length;
        const flaggedThree = neighborsThree.filter(n => n.tile.isFlagged).length;

        const unopenedOne = neighborsOne.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedTwo = neighborsTwo.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedThree = neighborsThree.filter(n => !n.tile.isOpened && !n.tile.isFlagged);

        if (flaggedOne === 0 && flaggedTwo === 0 && flaggedThree === 0) {
            const sharedOneTwo = unopenedOne.filter(n1 => unopenedTwo.some(n2 => n1.x === n2.x && n1.y === n2.y));
            const sharedTwoThree = unopenedTwo.filter(n1 => unopenedThree.some(n2 => n1.x === n2.x && n1.y === n2.y));
            const uniqueThree = unopenedThree.filter(n => !sharedTwoThree.some(s => s.x === n.x && s.y === n.y));

            if (uniqueThree.length === 3 - sharedTwoThree.length) {
                uniqueThree.forEach(n => {
                    if (!n.tile.isFlagged && flagCount < MAX_FLAGS) {
                        log(`Hàng đợi gắn cờ tại (${n.x}, ${n.y}) dựa trên mẫu 1-2-3`);
                        actionQueue.push(async () => {
                            const success = await triggerClick(n.tile.element, true);
                            if (success) {
                                n.tile.isFlagged = true;
                            }
                        });
                        actionTaken = true;
                    }
                });
            }
        }

        return actionTaken;
    }

    async function detect1231Pattern(grid) {
        let actionTaken = false;

        for (let i = 0; i < grid.length; i++) {
            for (let j = 0; j < grid[i].length - 3; j++) {
                if (checkPattern(grid, i, j, i, j+3, [1,2,3,1])) {
                    actionTaken = actionTaken || await solve1231Pattern(grid, {x: i, y: j}, {x: i, y: j+1}, {x: i, y: j+2}, {x: i, y: j+3});
                }
            }
        }

        for (let i = 0; i < grid.length - 3; i++) {
            for (let j = 0; j < grid[i].length; j++) {
                if (checkPattern(grid, i, j, i+3, j, [1,2,3,1])) {
                    actionTaken = actionTaken || await solve1231Pattern(grid, {x: i, y: j}, {x: i+1, y: j}, {x: i+2, y: j}, {x: i+3, y: j});
                }
            }
        }

        return actionTaken;
    }

    async function solve1231Pattern(grid, one1, two, three, one2) {
        let actionTaken = false;

        const neighborsOne1 = getNeighbors(grid, one1.x, one1.y);
        const neighborsTwo = getNeighbors(grid, two.x, two.y);
        const neighborsThree = getNeighbors(grid, three.x, three.y);
        const neighborsOne2 = getNeighbors(grid, one2.x, one2.y);

        const flaggedOne1 = neighborsOne1.filter(n => n.tile.isFlagged).length;
        const flaggedTwo = neighborsTwo.filter(n => n.tile.isFlagged).length;
        const flaggedThree = neighborsThree.filter(n => n.tile.isFlagged).length;
        const flaggedOne2 = neighborsOne2.filter(n => n.tile.isFlagged).length;

        const unopenedOne1 = neighborsOne1.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedTwo = neighborsTwo.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedThree = neighborsThree.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedOne2 = neighborsOne2.filter(n => !n.tile.isOpened && !n.tile.isFlagged);

        if (flaggedOne1 === 0 && flaggedTwo === 0 && flaggedThree === 0 && flaggedOne2 === 0) {
            const sharedTwoThree = unopenedTwo.filter(n1 => unopenedThree.some(n2 => n1.x === n2.x && n1.y === n2.y));
            const uniqueThree = unopenedThree.filter(n => !sharedTwoThree.some(s => s.x === n.x && s.y === n.y));

            if (uniqueThree.length === 3 - sharedTwoThree.length) {
                uniqueThree.forEach(n => {
                    if (!n.tile.isFlagged && flagCount < MAX_FLAGS) {
                        log(`Hàng đợi gắn cờ tại (${n.x}, ${n.y}) dựa trên mẫu 1-2-3-1`);
                        actionQueue.push(async () => {
                            const success = await triggerClick(n.tile.element, true);
                            if (success) {
                                n.tile.isFlagged = true;
                            }
                        });
                        actionTaken = true;
                    }
                });
            }
        }

        return actionTaken;
    }

    async function detect12321Pattern(grid) {
        let actionTaken = false;

        for (let i = 0; i < grid.length; i++) {
            for (let j = 0; j < grid[i].length - 4; j++) {
                if (checkPattern(grid, i, j, i, j+4, [1,2,3,2,1])) {
                    actionTaken = actionTaken || await solve12321Pattern(grid, {x: i, y: j}, {x: i, y: j+1}, {x: i, y: j+2}, {x: i, y: j+3}, {x: i, y: j+4});
                }
            }
        }

        for (let i = 0; i < grid.length - 4; i++) {
            for (let j = 0; j < grid[i].length; j++) {
                if (checkPattern(grid, i, j, i+4, j, [1,2,3,2,1])) {
                    actionTaken = actionTaken || await solve12321Pattern(grid, {x: i, y: j}, {x: i+1, y: j}, {x: i+2, y: j}, {x: i+3, y: j}, {x: i+4, y: j});
                }
            }
        }

        return actionTaken;
    }

    async function solve12321Pattern(grid, one1, two1, three, two2, one2) {
        let actionTaken = false;

        const neighborsOne1 = getNeighbors(grid, one1.x, one1.y);
        const neighborsTwo1 = getNeighbors(grid, two1.x, two1.y);
        const neighborsThree = getNeighbors(grid, three.x, three.y);
        const neighborsTwo2 = getNeighbors(grid, two2.x, two2.y);
        const neighborsOne2 = getNeighbors(grid, one2.x, one2.y);

        const flaggedOne1 = neighborsOne1.filter(n => n.tile.isFlagged).length;
        const flaggedTwo1 = neighborsTwo1.filter(n => n.tile.isFlagged).length;
        const flaggedThree = neighborsThree.filter(n => n.tile.isFlagged).length;
        const flaggedTwo2 = neighborsTwo2.filter(n => n.tile.isFlagged).length;
        const flaggedOne2 = neighborsOne2.filter(n => n.tile.isFlagged).length;

        const unopenedOne1 = neighborsOne1.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedTwo1 = neighborsTwo1.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedThree = neighborsThree.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedTwo2 = neighborsTwo2.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedOne2 = neighborsOne2.filter(n => !n.tile.isOpened && !n.tile.isFlagged);

        if (flaggedOne1 === 0 && flaggedTwo1 === 0 && flaggedThree === 0 && flaggedTwo2 === 0 && flaggedOne2 === 0) {
            const sharedTwo1Three = unopenedTwo1.filter(n1 => unopenedThree.some(n2 => n1.x === n2.x && n1.y === n2.y));
            const sharedThreeTwo2 = unopenedThree.filter(n1 => unopenedTwo2.some(n2 => n1.x === n2.x && n1.y === n2.y));
            const uniqueThree = unopenedThree.filter(n =>
                !sharedTwo1Three.some(s => s.x === n.x && s.y === n.y) &&
                !sharedThreeTwo2.some(s => s.x === n.x && s.y === n.y));

            if (uniqueThree.length === 3 - (sharedTwo1Three.length + sharedThreeTwo2.length)) {
                uniqueThree.forEach(n => {
                    if (!n.tile.isFlagged && flagCount < MAX_FLAGS) {
                        log(`Hàng đợi gắn cờ tại (${n.x}, ${n.y}) dựa trên mẫu 1-2-3-2-1`);
                        actionQueue.push(async () => {
                            const success = await triggerClick(n.tile.element, true);
                            if (success) {
                                n.tile.isFlagged = true;
                            }
                        });
                        actionTaken = true;
                    }
                });
            }
        }

        return actionTaken;
    }

    async function detect242Pattern(grid) {
        let actionTaken = false;

        for (let i = 0; i < grid.length; i++) {
            for (let j = 0; j < grid[i].length - 2; j++) {
                if (checkPattern(grid, i, j, i, j+2, [2,4,2])) {
                    actionTaken = actionTaken || await solve242Pattern(grid, {x: i, y: j}, {x: i, y: j+1}, {x: i, y: j+2});
                }
            }
        }

        for (let i = 0; i < grid.length - 2; i++) {
            for (let j = 0; j < grid[i].length; j++) {
                if (checkPattern(grid, i, j, i+2, j, [2,4,2])) {
                    actionTaken = actionTaken || await solve242Pattern(grid, {x: i, y: j}, {x: i+1, y: j}, {x: i+2, y: j});
                }
            }
        }

        return actionTaken;
    }

    async function solve242Pattern(grid, two1, four, two2) {
        let actionTaken = false;

        const neighborsTwo1 = getNeighbors(grid, two1.x, two1.y);
        const neighborsFour = getNeighbors(grid, four.x, four.y);
        const neighborsTwo2 = getNeighbors(grid, two2.x, two2.y);

        const flaggedTwo1 = neighborsTwo1.filter(n => n.tile.isFlagged).length;
        const flaggedFour = neighborsFour.filter(n => n.tile.isFlagged).length;
        const flaggedTwo2 = neighborsTwo2.filter(n => n.tile.isFlagged).length;

        const unopenedTwo1 = neighborsTwo1.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedFour = neighborsFour.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedTwo2 = neighborsTwo2.filter(n => !n.tile.isOpened && !n.tile.isFlagged);

        if (flaggedTwo1 === 0 && flaggedFour === 0 && flaggedTwo2 === 0) {
            const sharedTwo1Four = unopenedTwo1.filter(n1 => unopenedFour.some(n2 => n1.x === n2.x && n1.y === n2.y));
            const sharedFourTwo2 = unopenedFour.filter(n1 => unopenedTwo2.some(n2 => n1.x === n2.x && n1.y === n2.y));
            const uniqueFour = unopenedFour.filter(n =>
                                                   !sharedTwo1Four.some(s => s.x === n.x && s.y === n.y) &&
                                                   !sharedFourTwo2.some(s => s.x === n.x && s.y === n.y));

            if (uniqueFour.length === 4 - (sharedTwo1Four.length + sharedFourTwo2.length)) {
                uniqueFour.forEach(n => {
                    if (!n.tile.isFlagged && flagCount < MAX_FLAGS) {
                        log(`Hàng đợi gắn cờ tại (${n.x}, ${n.y}) dựa trên mẫu 2-4-2`);
                        actionQueue.push(async () => {
                            const success = await triggerClick(n.tile.element, true);
                            if (success) {
                                n.tile.isFlagged = true;
                            }
                        });
                        actionTaken = true;
                    }
                });
            }
        }

        return actionTaken;
    }

    async function detect424Pattern(grid) {
        let actionTaken = false;

        for (let i = 0; i < grid.length; i++) {
            for (let j = 0; j < grid[i].length - 2; j++) {
                if (checkPattern(grid, i, j, i, j+2, [4,2,4])) {
                    actionTaken = actionTaken || await solve424Pattern(grid, {x: i, y: j}, {x: i, y: j+1}, {x: i, y: j+2});
                }
            }
        }

        for (let i = 0; i < grid.length - 2; i++) {
            for (let j = 0; j < grid[i].length; j++) {
                if (checkPattern(grid, i, j, i+2, j, [4,2,4])) {
                    actionTaken = actionTaken || await solve424Pattern(grid, {x: i, y: j}, {x: i+1, y: j}, {x: i+2, y: j});
                }
            }
        }

        return actionTaken;
    }

    async function solve424Pattern(grid, four1, two, four2) {
        let actionTaken = false;

        const neighborsFour1 = getNeighbors(grid, four1.x, four1.y);
        const neighborsTwo = getNeighbors(grid, two.x, two.y);
        const neighborsFour2 = getNeighbors(grid, four2.x, four2.y);

        const flaggedFour1 = neighborsFour1.filter(n => n.tile.isFlagged).length;
        const flaggedTwo = neighborsTwo.filter(n => n.tile.isFlagged).length;
        const flaggedFour2 = neighborsFour2.filter(n => n.tile.isFlagged).length;

        const unopenedFour1 = neighborsFour1.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedTwo = neighborsTwo.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedFour2 = neighborsFour2.filter(n => !n.tile.isOpened && !n.tile.isFlagged);

        if (flaggedFour1 === 0 && flaggedTwo === 0 && flaggedFour2 === 0) {
            const sharedFour1Two = unopenedFour1.filter(n1 => unopenedTwo.some(n2 => n1.x === n2.x && n1.y === n2.y));
            const sharedTwoFour2 = unopenedTwo.filter(n1 => unopenedFour2.some(n2 => n1.x === n2.x && n1.y === n2.y));
            const uniqueTwo = unopenedTwo.filter(n =>
                                                 !sharedFour1Two.some(s => s.x === n.x && s.y === n.y) &&
                                                 !sharedTwoFour2.some(s => s.x === n.x && s.y === n.y));

            if (uniqueTwo.length === 2 - (sharedFour1Two.length + sharedTwoFour2.length)) {
                uniqueTwo.forEach(n => {
                    if (!n.tile.isFlagged && flagCount < MAX_FLAGS) {
                        log(`Hàng đợi gắn cờ tại (${n.x}, ${n.y}) dựa trên mẫu 4-2-4`);
                        actionQueue.push(async () => {
                            const success = await triggerClick(n.tile.element, true);
                            if (success) {
                                n.tile.isFlagged = true;
                            }
                        });
                        actionTaken = true;
                    }
                });
            }
        }

        return actionTaken;
    }

    async function detect245Pattern(grid) {
        let actionTaken = false;

        for (let i = 0; i < grid.length; i++) {
            for (let j = 0; j < grid[i].length - 2; j++) {
                if (checkPattern(grid, i, j, i, j+2, [2,4,5])) {
                    actionTaken = actionTaken || await solve245Pattern(grid, {x: i, y: j}, {x: i, y: j+1}, {x: i, y: j+2});
                }
            }
        }

        for (let i = 0; i < grid.length - 2; i++) {
            for (let j = 0; j < grid[i].length; j++) {
                if (checkPattern(grid, i, j, i+2, j, [2,4,5])) {
                    actionTaken = actionTaken || await solve245Pattern(grid, {x: i, y: j}, {x: i+1, y: j}, {x: i+2, y: j});
                }
            }
        }

        return actionTaken;
    }

    async function solve245Pattern(grid, two, four, five) {
        let actionTaken = false;

        const neighborsTwo = getNeighbors(grid, two.x, two.y);
        const neighborsFour = getNeighbors(grid, four.x, four.y);
        const neighborsFive = getNeighbors(grid, five.x, five.y);

        const flaggedTwo = neighborsTwo.filter(n => n.tile.isFlagged).length;
        const flaggedFour = neighborsFour.filter(n => n.tile.isFlagged).length;
        const flaggedFive = neighborsFive.filter(n => n.tile.isFlagged).length;

        const unopenedTwo = neighborsTwo.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedFour = neighborsFour.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedFive = neighborsFive.filter(n => !n.tile.isOpened && !n.tile.isFlagged);

        if (flaggedTwo === 0 && flaggedFour === 0 && flaggedFive === 0) {
            const sharedTwoFour = unopenedTwo.filter(n1 => unopenedFour.some(n2 => n1.x === n2.x && n1.y === n2.y));
            const sharedFourFive = unopenedFour.filter(n1 => unopenedFive.some(n2 => n1.x === n2.x && n1.y === n2.y));
            const uniqueFive = unopenedFive.filter(n => !sharedFourFive.some(s => s.x === n.x && s.y === n.y));

            if (uniqueFive.length === 5 - sharedFourFive.length) {
                uniqueFive.forEach(n => {
                    if (!n.tile.isFlagged && flagCount < MAX_FLAGS) {
                        log(`Hàng đợi gắn cờ tại (${n.x}, ${n.y}) dựa trên mẫu 2-4-5`);
                        actionQueue.push(async () => {
                            const success = await triggerClick(n.tile.element, true);
                            if (success) {
                                n.tile.isFlagged = true;
                            }
                        });
                        actionTaken = true;
                    }
                });
            }
        }

        return actionTaken;
    }

    async function detect454Pattern(grid) {
        let actionTaken = false;

        for (let i = 0; i < grid.length; i++) {
            for (let j = 0; j < grid[i].length - 2; j++) {
                if (checkPattern(grid, i, j, i, j+2, [4,5,4])) {
                    actionTaken = actionTaken || await solve454Pattern(grid, {x: i, y: j}, {x: i, y: j+1}, {x: i, y: j+2});
                }
            }
        }

        for (let i = 0; i < grid.length - 2; i++) {
            for (let j = 0; j < grid[i].length; j++) {
                if (checkPattern(grid, i, j, i+2, j, [4,5,4])) {
                    actionTaken = actionTaken || await solve454Pattern(grid, {x: i, y: j}, {x: i+1, y: j}, {x: i+2, y: j});
                }
            }
        }

        return actionTaken;
    }

    async function solve454Pattern(grid, four1, five, four2) {
        let actionTaken = false;

        const neighborsFour1 = getNeighbors(grid, four1.x, four1.y);
        const neighborsFive = getNeighbors(grid, five.x, five.y);
        const neighborsFour2 = getNeighbors(grid, four2.x, four2.y);

        const flaggedFour1 = neighborsFour1.filter(n => n.tile.isFlagged).length;
        const flaggedFive = neighborsFive.filter(n => n.tile.isFlagged).length;
        const flaggedFour2 = neighborsFour2.filter(n => n.tile.isFlagged).length;

        const unopenedFour1 = neighborsFour1.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedFive = neighborsFive.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
        const unopenedFour2 = neighborsFour2.filter(n => !n.tile.isOpened && !n.tile.isFlagged);

        if (flaggedFour1 === 0 && flaggedFive === 0 && flaggedFour2 === 0) {
            const sharedFour1Five = unopenedFour1.filter(n1 => unopenedFive.some(n2 => n1.x === n2.x && n1.y === n2.y));
            const sharedFiveFour2 = unopenedFive.filter(n1 => unopenedFour2.some(n2 => n1.x === n2.x && n1.y === n2.y));
            const uniqueFive = unopenedFive.filter(n =>
                                                   !sharedFour1Five.some(s => s.x === n.x && s.y === n.y) &&
                                                   !sharedFiveFour2.some(s => s.x === n.x && s.y === n.y));

            if (uniqueFive.length === 5 - (sharedFour1Five.length + sharedFiveFour2.length)) {
                uniqueFive.forEach(n => {
                    if (!n.tile.isFlagged && flagCount < MAX_FLAGS) {
                        log(`Hàng đợi gắn cờ tại (${n.x}, ${n.y}) dựa trên mẫu 4-5-4`);
                        actionQueue.push(async () => {
                            const success = await triggerClick(n.tile.element, true);
                            if (success) {
                                n.tile.isFlagged = true;
                            }
                        });
                        actionTaken = true;
                    }
                });
            }
        }

        return actionTaken;
    }

    async function performTankSolving(grid) {
        let actionTaken = false;

        for (let i = 0; i < grid.length; i++) {
            for (let j = 0; j < grid[i].length; j++) {
                const tile = grid[i][j];
                if (!tile.isOpened || tile.value === 0) continue;

                const neighbors = getNeighbors(grid, i, j);
                const unopenedNeighbors = neighbors.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
                const flaggedNeighbors = neighbors.filter(n => n.tile.isFlagged);

                if (unopenedNeighbors.length === 0) continue;

                const remainingMines = tile.value - flaggedNeighbors.length;

                neighbors.filter(n => n.tile.isOpened && n.tile.value > 0).forEach(neighbor => {
                    const nx = neighbor.x;
                    const ny = neighbor.y;

                    const neighborNeighbors = getNeighbors(grid, nx, ny);
                    const neighborUnopenedNeighbors = neighborNeighbors.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
                    const neighborFlaggedNeighbors = neighborNeighbors.filter(n => n.tile.isFlagged);

                    const sharedUnopenedNeighbors = unopenedNeighbors.filter(n1 =>
                                                                             neighborUnopenedNeighbors.some(n2 => n1.x === n2.x && n1.y === n2.y));

                    if (sharedUnopenedNeighbors.length > 0) {
                        const remainingMines1 = tile.value - flaggedNeighbors.length;
                        const remainingMines2 = neighbor.tile.value - neighborFlaggedNeighbors.length;

                        const uniqueUnopenedNeighbors1 = unopenedNeighbors.filter(n1 =>
                                                                                  !sharedUnopenedNeighbors.some(s => s.x === n1.x && s.y === n1.y));
                        const uniqueUnopenedNeighbors2 = neighborUnopenedNeighbors.filter(n1 =>
                                                                                          !sharedUnopenedNeighbors.some(s => s.x === n1.x && s.y === n1.y));

                        if (remainingMines1 === unopenedNeighbors.length && remainingMines1 > 0) {
                            unopenedNeighbors.forEach(n => {
                                if (!n.tile.isFlagged && flagCount < MAX_FLAGS) {
                                    log(`Hàng đợi gắn cờ tại (${n.x}, ${n.y}) dựa trên phân tích tank`);
                                    actionQueue.push(async () => {
                                        const success = await triggerClick(n.tile.element, true);
                                        if (success) {
                                            n.tile.isFlagged = true;
                                        }
                                    });
                                    actionTaken = true;
                                }
                            });
                        } else if (remainingMines1 === 0 && unopenedNeighbors.length > 0) {
                            unopenedNeighbors.forEach(n => {
                                log(`Hàng đợi mở ô tại (${n.x}, ${n.y}) dựa trên phân tích tank`);
                                actionQueue.push(async () => {
                                    await triggerClick(n.tile.element);
                                });
                                actionTaken = true;
                            });
                        }

                        if (remainingMines1 - uniqueUnopenedNeighbors1.length === sharedUnopenedNeighbors.length &&
                            sharedUnopenedNeighbors.length > 0) {
                            sharedUnopenedNeighbors.forEach(n => {
                                if (!n.tile.isFlagged && flagCount < MAX_FLAGS) {
                                    log(`Hàng đợi gắn cờ tại (${n.x}, ${n.y}) dựa trên phân tích tank sâu`);
                                    actionQueue.push(async () => {
                                        const success = await triggerClick(n.tile.element, true);
                                        if (success) {
                                            n.tile.isFlagged = true;
                                        }
                                    });
                                    actionTaken = true;
                                }
                            });
                        }

                        if (remainingMines2 - uniqueUnopenedNeighbors2.length === sharedUnopenedNeighbors.length &&
                            uniqueUnopenedNeighbors2.length > 0) {
                            uniqueUnopenedNeighbors2.forEach(n => {
                                log(`Hàng đợi mở ô tại (${n.x}, ${n.y}) dựa trên phân tích tank sâu`);
                                actionQueue.push(async () => {
                                    await triggerClick(n.tile.element);
                                });
                                actionTaken = true;
                            });
                        }
                    }
                });
            }
        }

        return actionTaken;
    }

    async function probabilitySolving(grid) {
        const unopenedTiles = [];
        const probabilityMap = new Map();

        for (let i = 0; i < grid.length; i++) {
            for (let j = 0; j < grid[i].length; j++) {
                const tile = grid[i][j];
                if (!tile.isOpened && !tile.isFlagged) {
                    unopenedTiles.push({ x: i, y: j, tile: tile });
                    probabilityMap.set(`${i},${j}`, { count: 0, totalConstraints: 0 });
                }
            }
        }

        if (unopenedTiles.length === 0) return false;

        const remainingMines = MAX_FLAGS - flagCount;
        for (let i = 0; i < grid.length; i++) {
            for (let j = 0; j < grid[i].length; j++) {
                const tile = grid[i][j];
                if (!tile.isOpened || tile.value === 0) continue;

                const neighbors = getNeighbors(grid, i, j);
                const unopenedNeighbors = neighbors.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
                const flaggedNeighbors = neighbors.filter(n => n.tile.isFlagged);

                if (unopenedNeighbors.length === 0) continue;

                const remainingMinesTile = tile.value - flaggedNeighbors.length;
                const probability = remainingMinesTile / unopenedNeighbors.length;

                unopenedNeighbors.forEach(n => {
                    const key = `${n.x},${n.y}`;
                    const probData = probabilityMap.get(key);
                    probData.count += probability;
                    probData.totalConstraints += 1;
                });
            }
        }

        let lowestProb = 1;
        let safestTile = null;

        probabilityMap.forEach((value, key) => {
            if (value.totalConstraints > 0) {
                const avgProb = value.count / value.totalConstraints;
                if (avgProb < lowestProb) {
                    lowestProb = avgProb;
                    const [x, y] = key.split(',').map(Number);
                    safestTile = unopenedTiles.find(t => t.x === x && t.y === y);
                }
            }
        });

        if (safestTile && lowestProb < 0.3) {
            log(`Hàng đợi mở ô tại (${safestTile.x}, ${safestTile.y}) với xác suất ${lowestProb.toFixed(2)}`);
            actionQueue.push(async () => {
                await triggerClick(safestTile.tile.element);
            });
            return true;
        } else if (safestTile) {
            log(`Không có nước đi chắc chắn, hàng đợi đoán ô an toàn nhất tại (${safestTile.x}, ${safestTile.y}) với xác suất ${lowestProb.toFixed(2)}`);
            actionQueue.push(async () => {
                await triggerClick(safestTile.tile.element);
            });
            return true;
        }

        const cornerTiles = [
            grid[0][0], grid[0][grid[0].length - 1],
            grid[grid.length - 1][0], grid[grid.length - 1][grid[0].length - 1]
        ].filter(t => !t.isOpened && !t.isFlagged);
        if (cornerTiles.length > 0) {
            const randomTile = cornerTiles[Math.floor(Math.random() * cornerTiles.length)];
            log(`Không có nước đi an toàn, hàng đợi đoán ngẫu nhiên tại (${randomTile.index / 10}, ${randomTile.index % 10})`);
            actionQueue.push(async () => {
                await triggerClick(randomTile.element);
            });
            return true;
        }

        log("Không tìm thấy nước đi nào khả thi");
        return false;
    }

    async function makeFirstMove(grid) {
        if (!grid) return false;

        const centerX = Math.floor(grid.length / 2);
        const centerY = Math.floor(grid[0].length / 2);

        if (!grid[centerX][centerY].isOpened) {
            log(`Hàng đợi bước đi đầu tiên ở trung tâm (${centerX}, ${centerY})`);
            actionQueue.push(async () => {
                await triggerClick(grid[centerX][centerY].element);
            });
            return true;
        }

        for (let radius = 1; radius < Math.max(grid.length, grid[0].length); radius++) {
            for (let i = -radius; i <= radius; i++) {
                for (let j = -radius; j <= radius; j++) {
                    if (Math.abs(i) === radius || Math.abs(j) === radius) {
                        const x = centerX + i;
                        const y = centerY + j;
                        if (x >= 0 && x < grid.length && y >= 0 && y < grid[0].length &&
                            !grid[x][y].isOpened && !grid[x][y].isFlagged) {
                            log(`Hàng đợi bước đi đầu tiên gần trung tâm tại (${x}, ${y})`);
                            actionQueue.push(async () => {
                                await triggerClick(grid[x][y].element);
                            });
                            return true;
                        }
                    }
                }
            }
        }

        return false;
    }

    function checkGameStatus() {
        const gameInfo = document.querySelector('.ms-info');
        if (gameInfo && gameInfo.textContent.includes('Game Over')) {
            log("Đã phát hiện trò chơi kết thúc");
            return 'game-over';
        }

        const gameEndMsg = document.querySelector('.game-end-message, .game-complete');
        if (gameEndMsg) {
            log("Trò chơi đã hoàn tất thành công");
            return 'completed';
        }

        const grid = getGrid();
        if (!grid) {
            log("No grid found during status check");
            return 'not-started';
        }

        let unopenedCount = 0;
        for (let i = 0; i < grid.length; i++) {
            for (let j = 0; j < grid[i].length; j++) {
                if (!grid[i][j].isOpened && !grid[i][j].isFlagged) unopenedCount++;
            }
        }

        if (unopenedCount === 0) {
            log("Tất cả các ô đã mở hoặc được đánh dấu - trò chơi đã hoàn tất");
            return 'completed';
        }

        log("Game in progress");
        return 'in-progress';
    }

    function checkUnsolvable(grid) {
        const remainingMines = MAX_FLAGS - flagCount;
        const unopenedCount = grid.flat().filter(t => !t.isOpened && !t.isFlagged).length;

        if (remainingMines > unopenedCount) {
            log(`Không thể giải: Còn ${remainingMines} mìn nhưng chỉ có ${unopenedCount} ô chưa mở`);
            return true;
        }

        for (let i = 0; i < grid.length; i++) {
            for (let j = 0; j < grid[i].length; j++) {
                const tile = grid[i][j];
                if (tile.isOpened && tile.value > 0) {
                    const neighbors = getNeighbors(grid, i, j);
                    const unopenedNeighbors = neighbors.filter(n => !n.tile.isOpened && !n.tile.isFlagged);
                    const flaggedNeighbors = neighbors.filter(n => n.tile.isFlagged);
                    const requiredMines = tile.value - flaggedNeighbors.length;
                    if (requiredMines > unopenedNeighbors.length) {
                        log(`Không thể giải: Ô (${i}, ${j}) cần ${requiredMines} mìn nhưng chỉ có ${unopenedNeighbors.length} ô chưa mở`);
                        return true;
                    }
                    if (requiredMines > remainingMines) {
                        log(`Không thể giải: Ô (${i}, ${j}) cần ${requiredMines} mìn nhưng chỉ còn ${remainingMines} mìn toàn cục`);
                        return true;
                    }
                }
            }
        }
        return false;
    }

    async function solveStep() {
        const gameStatus = checkGameStatus();
        if (gameStatus === 'game-over') {
            log("Trò chơi kết thúc, lên lịch tải lại sau 10 giây");
            setTimeout(() => window.location.reload(), RELOAD_DELAY);
            return;
        }
        if (gameStatus === 'completed') {
            log("Game complete! Looking for continue button");
            setTimeout(clickContinue, 1000);
            return;
        }
        if (gameStatus === 'not-started') {
            log("Trò chơi chưa bắt đầu, đang cố gắng bắt đầu");
            setTimeout(startGame, 1000);
            return;
        }

        let grid = getGrid();
        if (!grid) {
            log("No grid found, retrying in 1 second");
            setTimeout(solveStep, 1000);
            return;
        }

        if (checkUnsolvable(grid)) {
            log("Ván chơi không thể giải, reload sau 5 giây");
            setTimeout(() => window.location.reload(), 5000);
            return;
        }

        const remainingMines = MAX_FLAGS - flagCount;
        const unopenedCount = grid.flat().filter(t => !t.isOpened && !t.isFlagged).length;
        if (remainingMines === unopenedCount && remainingMines > 0) {
            grid.flat().forEach(tile => {
                if (!tile.isOpened && !tile.isFlagged && flagCount < MAX_FLAGS) {
                    log(`Hàng đợi đánh cờ ô cuối cùng tại (${tile.index / 10}, ${tile.index % 10})`);
                    actionQueue.push(async () => {
                        const success = await triggerClick(tile.element, true);
                        if (success) {
                            tile.isFlagged = true;
                        }
                    });
                }
            });
            await processActionQueue();
            setTimeout(solveStep, SOLVE_DELAY);
            return;
        }
        let actionTaken = false;

        const anyOpened = grid.some(row => row.some(tile => tile.isOpened));
        if (!anyOpened) {
            actionTaken = await makeFirstMove(grid);
            if (actionTaken) {
                log("Đã thực hiện bước đi đầu tiên, chờ đợi để xem kết quả");
                await processActionQueue();
                setTimeout(solveStep, SOLVE_DELAY);
                return;
            }
        }

        if (!actionTaken) actionTaken = await basicSolve(grid);
        if (!actionTaken) actionTaken = await advancedPatternAnalysis(grid);
        if (!actionTaken) actionTaken = await probabilitySolving(grid);

        if (actionTaken) {
            log("Hành động đã được hàng đợi, xử lý lần lượt");
            await processActionQueue();
            setTimeout(solveStep, SOLVE_DELAY);
        } else {
            setTimeout(solveStep, 1000);
        }
    }

    function checkGameReady() {
        const gameStatus = checkGameStatus();
        if (gameStatus === 'game-over') {
            log("Game Over detected during ready check, scheduling reload");
            setTimeout(() => window.location.reload(), RELOAD_DELAY);
            return;
        }

        const infoBar = document.querySelector('.ms-infobar');
        if (infoBar) {
            if (infoBar.textContent.includes('Max Daily Gameplay Reached')) {
                log("Đã hết lượt chơi game");
                return;
            } else if (infoBar.textContent.includes('Game Ready')) {
                log("Trò chơi đã sẵn sàng, bắt đầu trong 2 giây");
                setTimeout(solveStep, 2000);
            } else {
                log("Trò chơi chưa sẵn sàng, kiểm tra lại sau 1 giây");
                setTimeout(checkGameReady, 1000);
            }
        } else {
            setTimeout(checkGameReady, 1000);
        }
    }

    async function clickContinue() {
        const continueButton = document.querySelector('.fPSBzf.bYPztT.bYPznK.pezuA.cMGtQw.pBppg.dMMuNs button');
        if (continueButton && continueButton.textContent.trim() === "Continue") {
            log("Tìm thấy nút 'Continue', hàng đợi click...");
            actionQueue.push(async () => {
                await triggerClick(continueButton);
            });
            await processActionQueue();
            setTimeout(checkGameReady, 1000);
        } else {
            log("Không tìm thấy nút 'Continue'...");
            checkGameReady();
        }
    }

    async function startGame(attempts = 10) {
        const gameStatus = checkGameStatus();
        log(`Game status: ${gameStatus}`);

        if (gameStatus === 'game-over') {
            setTimeout(() => window.location.reload(), RELOAD_DELAY);
            return;
        }
        if (gameStatus === 'in-progress' || gameStatus === 'completed') {
            log("Trò chơi đã bắt đầu hoặc đã hoàn tất, tiến tới bước tiếp theo");
            setTimeout(checkGameReady, 1000);
            return;
        }

        log("Đang tìm nút 'Playnow'");
        const playButtons = document.querySelectorAll('button');
        let playButton = null;
        playButtons.forEach(btn => {
            if (btn.textContent.trim().toLowerCase() === "play now") {
                playButton = btn;
            }
        });

        if (playButton) {
            log("Tìm thấy nút 'Play now', hàng đợi click sau 2 giây");
            actionQueue.push(async () => {
                await triggerClick(playButton);
            });
            setTimeout(async () => {
                await processActionQueue();
                setTimeout(clickContinue, 3000);
            }, 2000);
        } else if (attempts > 0) {
            log(`Không tìm thấy nút 'Play now', đang thử lại (${attempts} lần thử còn lại)`);
            setTimeout(() => startGame(attempts - 1), 1000);
        } else {
            setTimeout(clickContinue, 1000);
        }
    }

    log("Dân Cày Airdrop");
    setTimeout(startGame, 2000);
})();'''
        start_time = time.time()
        is_popup = True
        try_play = 3
        while try_play > 0:
            # Check for game ready status using class name
            if not self.node.find_and_click(By.XPATH, '//p[contains(text(),"Play now")]', timeout=20):
                # close all popup
                if is_popup:
                    self.node.find_and_click(By.XPATH, '//button[div[text()="Continue"]]', timeout=20)
                    is_popup = False
                text = self.node.get_text(By.CLASS_NAME, 'ms-info')
                if text and 'Game Ready' in text:
                    start_time = time.time()
                    self.driver.execute_script(js)
                elif text and 'Game In Progress' in text:
                    self.node.log(f'Đang chơi dò mìn')
                elif text and 'Game Over' in text:
                    self.node.reload_tab()
                    try_play -= 1
                elif text and 'Max Daily Gameplay Reached' in text:
                    self.node.snapshot(f'Đạt giới hạn chơi dò mìn hôm nay')
                    break
                else:
                    self.node.snapshot(f'Lỗi khi chơi dò mìn')
                    return False

            if time.time() - start_time > 300:
                self.node.reload_tab()
                try_play -= 1

        self.node.snapshot(f'Hoàn thành cố gắng chơi 3 lần dò mìn')
        return True

    def _run(self):
        self.node.go_to('https://www.magicnewton.com/portal/rewards')
        if self.node.find(By.XPATH, f'//p[contains(text(), "{self.email}")]'):
            self.node.log(f'{self.profile_name} đã đăng nhập')
        else:
            self.node.snapshot(f'{self.profile_name} chưa đăng nhập')
        self.roll_dice()
        self.play_minesweeper()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--auto', action='store_true', help="Chạy ở chế độ tự động")
    parser.add_argument('--headless', action='store_true', help="Chạy trình duyệt ẩn")
    parser.add_argument('--disable-gpu', action='store_true', help="Tắt GPU")
    args = parser.parse_args()

    profiles = Utility.get_data('profile_name', 'email')
    if not profiles:
        print("Không có dữ liệu để chạy")
        exit()

    browser_manager = BrowserManager(AutoHandlerClass=Auto, SetupHandlerClass=Setup)
    # browser_manager.run_browser(profiles[1])
    browser_manager.run_terminal(
        profiles=profiles,
        max_concurrent_profiles=4,
        block_media=False,
        auto=args.auto,
        headless=args.headless,
        disable_gpu=args.disable_gpu,
    )