-- Schema for the `readforyou` MySQL database (structure only, no data).

CREATE TABLE IF NOT EXISTS `tasks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `userId` varchar(64) COLLATE utf8mb4_general_ci NOT NULL,
  `requestId` varchar(64) COLLATE utf8mb4_general_ci NOT NULL,
  `dateTime` datetime NOT NULL,
  `bookName` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  `pageRange` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `status` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
