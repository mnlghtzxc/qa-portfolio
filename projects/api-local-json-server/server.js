const jsonServer = require("json-server");
const server = jsonServer.create();
const router = jsonServer.router("db.json");
const middlewares = jsonServer.defaults();

server.use(middlewares);
server.use(jsonServer.bodyParser);

// Вспомогательная функция валидации полей поста
function validatePostFields(postData, requireAll = true) {
  const errors = [];
  const { title, body, userId } = postData;

  // Если требуется наличие всех полей (POST/PUT), проверим, что они есть
  if (requireAll) {
    if (title === undefined) errors.push("title is required");
    if (body === undefined) errors.push("body is required");
    if (userId === undefined) errors.push("userId is required");
  }

  // Валидация title (если передан)
  if (title !== undefined) {
    if (typeof title !== "string" || title.trim() === "") {
      errors.push("title must be non-empty string");
    } else if (title.length > 100) {
      errors.push("title max length is 100");
    }
  }

  // Валидация body (если передан)
  if (body !== undefined) {
    if (typeof body !== "string" || body.trim() === "") {
      errors.push("body must be non-empty string");
    } else if (body.length > 1000) {
      errors.push("body max length is 1000");
    }
  }

  // Валидация userId (если передан)
  if (userId !== undefined) {
    if (typeof userId !== "number" || !Number.isInteger(userId) || userId <= 0) {
      errors.push("userId must be positive integer");
    }
  }

  // Проверка лишних полей
  const allowedFields = ["title", "body", "userId"];
  const extraFields = Object.keys(postData).filter(key => !allowedFields.includes(key));
  if (extraFields.length > 0) {
    errors.push(`unexpected fields: ${extraFields.join(", ")}`);
  }

  return errors;
}

// POST /posts — создание
server.post("/posts", (req, res, next) => {
  if (!req.body || typeof req.body !== "object" || Array.isArray(req.body)) {
    return res.status(400).json({ message: "Body must be valid JSON object" });
  }

  const errors = validatePostFields(req.body, true);
  if (errors.length > 0) {
    return res.status(400).json({ message: "Validation error", errors });
  }

  next();
});

// PUT /posts/:id — полное обновление
server.put("/posts/:id", (req, res, next) => {
  const id = parseInt(req.params.id);
  const post = router.db.get("posts").getById(id).value();

  if (!post) {
    return res.status(404).json({ message: "Post not found" });
  }

  if (!req.body || typeof req.body !== "object" || Array.isArray(req.body)) {
    return res.status(400).json({ message: "Body must be valid JSON object" });
  }

  const errors = validatePostFields(req.body, true);
  if (errors.length > 0) {
    return res.status(400).json({ message: "Validation error", errors });
  }

  next();
});

// PATCH /posts/:id — частичное обновление
server.patch("/posts/:id", (req, res, next) => {
  const id = parseInt(req.params.id);
  const post = router.db.get("posts").getById(id).value();

  if (!post) {
    return res.status(404).json({ message: "Post not found" });
  }

  if (!req.body || typeof req.body !== "object" || Array.isArray(req.body)) {
    return res.status(400).json({ message: "Body must be valid JSON object" });
  }

  const receivedFields = Object.keys(req.body);
  if (receivedFields.length === 0) {
    return res.status(400).json({ message: "Validation error", errors: ["No fields to update"] });
  }

  const errors = validatePostFields(req.body, false);
  if (errors.length > 0) {
    return res.status(400).json({ message: "Validation error", errors });
  }

  next();
});

// Обработка GET /posts/:id — возвращать 404, если не найден
server.get("/posts/:id", (req, res, next) => {
  const id = parseInt(req.params.id);
  const post = router.db.get("posts").getById(id).value();
  if (!post) {
    return res.status(404).json({ message: "Post not found" });
  }
  next();
});

// Обработка DELETE /posts/:id — возвращать 404, если не найден
server.delete("/posts/:id", (req, res, next) => {
  const id = parseInt(req.params.id);
  const post = router.db.get("posts").getById(id).value();
  if (!post) {
    return res.status(404).json({ message: "Post not found" });
  }
  next();
});

server.use(router);

server.listen(3000, () => {
  console.log("JSON Server running on port 3000");
});