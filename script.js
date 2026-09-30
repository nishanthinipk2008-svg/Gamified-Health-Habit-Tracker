const API_URL = "http://127.0.0.1:5000/api";

let currentUser = {
    id: 1,
    name: "Nisha"
};


// ===============================
// CREATE USER
// ===============================

async function createUser(name, email) {

    try {

        const response = await fetch(`${API_URL}/users`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: name,
                email: email
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Failed to create user");
        }

        currentUser.id = data.user_id;
        currentUser.name = data.name;

        localStorage.setItem(
            "userId",
            data.user_id
        );

        localStorage.setItem(
            "userName",
            data.name
        );

        return data;

    } catch (error) {

        console.error("Create User Error:", error);
        alert(error.message);

    }
}


// ===============================
// GET USER
// ===============================

async function getUser() {

    try {

        const response = await fetch(
            `${API_URL}/users/${currentUser.id}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Failed to get user");
        }

        return data;

    } catch (error) {

        console.error("Get User Error:", error);

    }
}


// ===============================
// ADD HABIT
// ===============================

async function addHabit(
    name,
    category,
    target = 1,
    xp = 10
) {

    try {

        const response = await fetch(
            `${API_URL}/habits`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    user_id: currentUser.id,
                    name: name,
                    category: category,
                    target: target,
                    xp: xp
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Failed to add habit"
            );
        }

        return data;

    } catch (error) {

        console.error("Add Habit Error:", error);

        alert(error.message);

    }
}


// ===============================
// GET HABITS
// ===============================

async function getHabits() {

    try {

        const response = await fetch(
            `${API_URL}/habits/${currentUser.id}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Failed to load habits"
            );
        }

        return data;

    } catch (error) {

        console.error("Get Habits Error:", error);

        return [];

    }
}


// ===============================
// COMPLETE HABIT
// ===============================

async function completeHabit(habitId) {

    try {

        const response = await fetch(
            `${API_URL}/habits/${habitId}/complete`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({})
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.message ||
                data.error ||
                "Failed to complete habit"
            );
        }

        return data;

    } catch (error) {

        console.error(
            "Complete Habit Error:",
            error
        );

        alert(error.message);

    }
}


// ===============================
// GET DASHBOARD
// ===============================

async function getDashboard() {

    try {

        const response = await fetch(
            `${API_URL}/dashboard/${currentUser.id}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error ||
                "Failed to load dashboard"
            );
        }

        updateDashboard(data);

        return data;

    } catch (error) {

        console.error(
            "Dashboard Error:",
            error
        );

    }
}


// ===============================
// UPDATE DASHBOARD UI
// ===============================

function updateDashboard(data) {

    const xpElement =
        document.getElementById("totalXP");

    const levelElement =
        document.getElementById("level");

    const streakElement =
        document.getElementById("streak");

    const habitElement =
        document.getElementById("totalHabits");

    const completedElement =
        document.getElementById("completedToday");


    if (xpElement) {
        xpElement.textContent =
            data.total_xp;
    }

    if (levelElement) {
        levelElement.textContent =
            data.level;
    }

    if (streakElement) {
        streakElement.textContent =
            data.streak;
    }

    if (habitElement) {
        habitElement.textContent =
            data.total_habits;
    }

    if (completedElement) {
        completedElement.textContent =
            data.completed_today;
    }
}


// ===============================
// GET ACHIEVEMENTS
// ===============================

async function getAchievements() {

    try {

        const response = await fetch(
            `${API_URL}/achievements/${currentUser.id}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error ||
                "Failed to load achievements"
            );
        }

        return data;

    } catch (error) {

        console.error(
            "Achievements Error:",
            error
        );

        return [];

    }
}


// ===============================
// ADD ACHIEVEMENT
// ===============================

async function addAchievement(
    title,
    description
) {

    try {

        const response = await fetch(
            `${API_URL}/achievements`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    user_id: currentUser.id,
                    title: title,
                    description: description
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error ||
                "Failed to add achievement"
            );
        }

        return data;

    } catch (error) {

        console.error(
            "Achievement Error:",
            error
        );

    }
}


// ===============================
// LOAD ALL DATA
// ===============================

async function loadTrackerData() {

    await getDashboard();

    const habits =
        await getHabits();

    const achievements =
        await getAchievements();

    console.log("Habits:", habits);

    console.log(
        "Achievements:",
        achievements
    );
}


// ===============================
// INITIALIZE
// ===============================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const savedUserId =
            localStorage.getItem("userId");

        const savedUserName =
            localStorage.getItem("userName");

        if (savedUserId) {

            currentUser.id =
                parseInt(savedUserId);

        }

        if (savedUserName) {

            currentUser.name =
                savedUserName;

        }

        loadTrackerData();

    }
);